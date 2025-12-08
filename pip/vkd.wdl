version 1.2

import "tasks/annotate.wdl"
import "tasks/compare.wdl"
import "tasks/download.wdl"
import "tasks/index.wdl"
import "tasks/normalize.wdl"

workflow vkd {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Compare multiple vcf against gold standard and generate a dataframe to resume information."
        outputs: {
            dataframe: {
                help: "Path where all variant information are store.",
            },
        }
    }

    parameter_meta {
        query_vcf_uri: {
            help: "Map associate a name to uri of vcf",
        }
        gold_std_vcf_uri: {
            help: "Uri to gold standard vcf.",
        }
        gold_std_bed_uri: {
            help: "Uri to gold standard confident region bed.",
        }
        reference_uri: {
            help: "Uri to reference genome.",
        }
        compare_tool: {
            help: "Which tools are use to perform vcf comparaison. If value not match suggests aardvark are used.",
            default: "aardvark",
            suggests: [
                "aardvark",
                "happy",
            ],
        }
        annotation_gff: {
            help: "Uri to genome annotation file in gff3 format.",
        }
        clinvar_version: {
            help: "Clinvar version in format: YYYYMMDD.",
        }
        run_snpeff: {
            help: "Annotate query vcf with snpeff.",
        }
        run_vep: {
            help: "Annotate query vcf with snpeff.",
        }
    }

    input {
        Map[String, String] query_vcf_uri
        String gold_std_vcf_uri
        String gold_std_bed_uri
        String reference_uri
        String compare_tool
        String annotation_gff
        String? clinvar_version
        Boolean? run_snpeff
        Boolean? run_vep
    }

    # Download annotation
    if (defined(clinvar_version)) {
        call download.clinvar {
            version = select_first([
                clinvar_version,
            ]),
        }
    }

    if (select_first([
        run_vep,
    ], false)) {

        call download.base as dl_annotation {
            uri = annotation_gff,
            filename = "annotation.gff.gz",
        }

        call index.tabix as gff_idx {
            path = dl_annotation.path,
            preset = "gff",
        }
    }

    # Download data
    call download.file_with_index as dl_gstd {
        uri = gold_std_vcf_uri,
        filename = "gold_std.vcf.gz",
        index = "tbi",
    }

    call download.base as dl_gstd_bed {
        uri = gold_std_bed_uri,
        filename = "gold_std.bed",
    }

    call download.file_with_index as dl_reference {
        uri = reference_uri,
        filename = "reference.fasta.gz",
        index = "fai",
    }

    call normalize.variant as gstd {
        vcf_path = dl_gstd.result.file,
        reference_path = dl_reference.result.file,
    }

    scatter (dataset_path in as_pairs(query_vcf_uri)) {
        call download.file_with_index as dl_query {
            uri = dataset_path.right,
            filename = dataset_path.left + ".vcf.gz",
            index = "tbi",
        }

        call normalize.variant as query {
            vcf_path = dl_query.result.file,
            reference_path = dl_reference.result.file,
        }

        if (select_first([
            run_snpeff,
        ], false)) {
            call annotate.snpeff {
                vcf = query.result.file,
                dataset_name = dataset_path.left,
            }
        }

        if (select_first([
            run_vep,
        ], false)) {
            call annotate.vep {
                vcf = query.result.file,
                reference_genome = dl_reference.result.file,
                dataset_name = dataset_path.left,
                gff = select_first([
                    gff_idx.result,
                ]),
            }
        }

        if (compare_tool == "hap.py") {
            call compare.happy {
                truth = gstd.result,
                query = query.result,
                confident_bed = dl_gstd_bed.path,
                reference_genome = dl_reference.result,
                output_name = dataset_path.left,

            }
        }
        if (compare_tool != "hap.py") {
            call compare.aardvark {
                truth = gstd.result,
                query = query.result,
                confident_bed = dl_gstd_bed.path,
                reference_genome = dl_reference.result,
                output_name = dataset_path.left,
            }
        }

        File query_vcf = query.result.file
        File query_vcf_label = if compare_tool == "hap.py" then happy.result.truth else aardvark.result.truth
        String dataset_name = dataset_path.left
    }

    call compare.merge {
        query = query_vcf,
        query_label = query_vcf_label,
        dataset = dataset_name,
        clinvar = clinvar.result.file,
    }

    output {
        File dataframe = merge.dataframe
    }
}
