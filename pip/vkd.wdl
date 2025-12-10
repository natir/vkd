version 1.2

import "tasks/compare.wdl"
import "tasks/download.wdl"
import "tasks/extract.wdl"
import "tasks/index.wdl"
import "tasks/normalize.wdl"
import "workflow/run_compare.wdl"

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
        target_chromosome: {
            help: "List of chromosome of interest",
        }
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
        Array[String] target_chromosome
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

    call normalize.variant as norm_gstd {
        vcf_path = dl_gstd.result.file,
        reference_path = dl_reference.result.file,
    }

    scatter (chromosome in target_chromosome) {
        call extract.chromosome as split_gstd_chr {
            variant = norm_gstd.result,
            target_chromosome = chromosome_name,
        }

        FileWithIndex gstd_chr = split_gstd_chr.result
        String chromosome_name = chromosome
    }

    scatter (dataset_pair in as_pairs(query_vcf_uri)) {
        call download.file_with_index as dl_query {
            uri = dataset_pair.right,
            filename = dataset_pair.left + ".vcf.gz",
            index = "tbi",
        }

        call normalize.variant as norm_query {
            vcf_path = dl_query.result.file,
            reference_path = dl_reference.result.file,
        }

        FileWithIndex query_file = norm_query.result
        String query_name = dataset_pair.left
    }

    scatter (name_gstd in zip(chromosome_name, gstd_chr)) {
        scatter (query_pair in zip(query_file, query_name)) {

          call extract.chromosome as query_chr {
                variant = query_pair.left,
                target_chromosome = name_gstd.left,
            }

            call run_compare.run_compare {
                gstd = name_gstd.right,
                reference = dl_reference.result,
                confident_bed = dl_gstd_bed.path,
                query = query_chr.result,
                query_name = query_pair.right,
                compare_tool = compare_tool,
                run_snpeff = select_first([
                    run_snpeff,
                ], false),
                run_vep = select_first([
                    run_vep,
                ], false),
                gff = gff_idx.result,
            }

            File query_vcf = run_compare.query_vcf
            File query_vcf_label = run_compare.query_vcf_label
            String dataset_name = run_compare.dataset_name
            String chr_name_out = name_gstd.left
	    File? snpeff_vcf = run_compare.snpeff_vcf
	    File? vep_vcf = run_compare.vep_vcf
        }

        call compare.merge {
            query = query_vcf,
            query_label = query_vcf_label,
            dataset = dataset_name,
            output_name = chr_name_out[0],
            clinvar = clinvar.result.file,
	  snpeff = snpeff_vcf,
	vep = vep_vcf,
        }

    }

    output {
        Array[File] dataframe = merge.dataframe
    }
}
