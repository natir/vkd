version 1.2

import "tasks/annotate.wdl"
import "tasks/compare.wdl"
import "tasks/download.wdl"
import "tasks/normalize_variant.wdl"

workflow vkd {
    input {
        Map[String, String] query_vcf_uri
        String gold_std_vcf_uri
        String gold_std_bed_uri
        String reference_uri
        String compare_tool
        String? clinvar_version
        Boolean? run_snpeff
        Boolean? run_vep
    }

    if (defined(clinvar_version)) {
        call download.clinvar { input:
            version = select_first([
                clinvar_version,
            ]),
        }
    }

    call download.vcf_with_index as dl_gstd { input:
        uri = gold_std_vcf_uri,
        path = "gold_std.vcf.gz",
    }

    call download.base as dl_gstd_bed { input:
        uri = gold_std_bed_uri,
        path = "gold_std.bed",
    }

    call download.fasta_with_index as dl_reference { input:
        uri = reference_uri,
        path = "reference.fasta.gz",
    }

    call normalize_variant.normalize_variant as gstd { input:
        vcf_path = dl_gstd.result.vcf,
        reference_path = dl_reference.result.fasta,
    }

    scatter (dataset_path in as_pairs(query_vcf_uri)) {
        call download.vcf_with_index as dl_query { input:
            uri = dataset_path.right,
            path = dataset_path.left + ".vcf.gz",
        }

        call normalize_variant.normalize_variant as query { input:
            vcf_path = dl_query.result.vcf,
            reference_path = dl_reference.result.fasta,
        }

        if (select_first([
            run_snpeff,
        ], false)) {
            call annotate.snpeff { input:
                vcf = query.result.vcf,
            }
        }

        if (select_first([
            run_vep,
        ], false)) {
            call annotate.vep { input:
                vcf = query.result.vcf,
            }
        }

        if (compare_tool == "hap.py") {
            call compare.happy {
                truth = gstd.result,
                query = query.result,
                confident_bed = dl_gstd_bed.out_path,
                reference_genome = dl_reference.result,
                output_name = dataset_path.left,
            }
        }
        if (compare_tool != "hap.py") {
            call compare.aardvark {
                truth = gstd.result,
                query = query.result,
                confident_bed = dl_gstd_bed.out_path,
                reference_genome = dl_reference.result,
                output_name = dataset_path.left,
            }
        }

        File query_vcf = query.result.vcf
        File query_vcf_label = if compare_tool == "hap.py" then happy.result.truth else aardvark.result.truth
        String version_ = dataset_path.left
    }

    call compare.merge { input:
        query = query_vcf,
        query_label = query_vcf_label,
        version = version_,
        clinvar = clinvar.result.vcf,
    }

    output {
        File summary = merge.dataframe
    }
}
