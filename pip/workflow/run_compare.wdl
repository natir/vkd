version 1.2

import "../tasks/annotate.wdl"
import "../tasks/compare.wdl"

workflow run_compare {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Compare multiple vcf against gold standard and generate a dataframe to resume information."
        outputs: {
            query_vcf: {
                help: "Path to query vcf.",
            },
            query_vcf_label: {
                help: "Path to query vcf labeled.",
            },
            dataset_name: {
                help: "Dataset name.",
            },
        }
    }

    parameter_meta {
        confident_bed: {
            help: "Gold standard of confident region bed.",
        }
        gstd: {
            help: "Gold standard variant file.",
        }
        reference: {
            help: "Reference file.",
        }
        query: {
            help: "Query variant file.",
        }
        query_name: {
            help: "Query dataset name.",
        }
        compare_tool: {
            help: "Which tools to compare.",
        }
        run_snpeff: {
            help: "Run snpeff.",
        }
        run_vep: {
            help: "Run vep.",
        }
        gff: {
            help: "Annotation of reference genome.",
        }
    }

    input {
        File confident_bed
        FileWithIndex gstd
        FileWithIndex reference
        FileWithIndex query
        String query_name
        String compare_tool
        Boolean run_snpeff
        Boolean run_vep
        FileWithIndex? gff
    }

    if (run_snpeff) {
        call annotate.snpeff {
            vcf = query.file,
            dataset_name = query_name,
        }
    }

    if (run_vep) {
        call annotate.vep {
            vcf = query.file,
            reference_genome = reference.file,
            dataset_name = query_name,
            gff = select_first([
                gff,
            ]),
        }
    }

    if (compare_tool == "hap.py") {
        call compare.happy {
            truth = gstd,
            query = query,
            confident_bed = confident_bed,
            reference_genome = reference,
            output_name = query_name,
        }
    }
    if (compare_tool != "hap.py") {
        call compare.aardvark {
            truth = gstd,
            query = query,
            confident_bed = confident_bed,
            reference_genome = reference,
            output_name = query_name,
        }
    }

    output {
        File query_vcf = query.file
        File query_vcf_label = if compare_tool == "hap.py" then happy.result.truth else aardvark.result.truth
        String dataset_name = query_name
    }
}
