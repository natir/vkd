version 1.2

import "../utils/types.wdl"

task aardvark {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Run aardvark to compare a truth vcf against a query."
        outputs: {
            result: {
                help: "File produce by aardvark.",
            },
        }
    }

    parameter_meta {
        confident_bed: {
            help: "Bed of trustable region.",
        }
        reference_genome: {
            help: "Reference genome in fasta with fasta index.",
        }
        truth: {
            help: "Truth vcf with index.",
        }
        query: {
            help: "Query vcf with index.",
        }
        output_name: {
            help: "Name of output directory.",
        }
    }

    input {
        File confident_bed
        FileWithIndex reference_genome
        FileWithIndex truth
        FileWithIndex query
        String output_name
    }

    command <<<
        aardvark compare --threads 4 --reference "~{reference_genome.file}" --truth-vcf "~{
            truth.file}" --query-vcf "~{query.file}" --regions "~{confident_bed}" --output-dir "~{
            output_name}"
    >>>

    output {
        VcfCompareOutput result = VcfCompareOutput {
            summary: "~{output_name}/summary.tsv",
            truth: "~{output_name}/truth.vcf.gz",
            query: "~{output_name}/query.vcf.gz",
        }
    }

    requirements {
        container: "quay.io/biocontainers/aardvark:0.10.2--h4349ce8_0"
        cpu: 8
    }
}

task happy {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Run hap.py to compare a truth vcf against a query."
        outputs: {
            result: {
                help: "File produce by hap.py.",
            },
        }
    }

    parameter_meta {
        confident_bed: {
            help: "Bed of trustable region.",
        }
        reference_genome: {
            help: "Reference genome in fasta with fasta index.",
        }
        truth: {
            help: "Truth vcf with index.",
        }
        query: {
            help: "Query vcf with index.",
        }
        output_name: {
            help: "Name of output directory.",
        }
    }

    input {
        File confident_bed
        FileWithIndex reference_genome
        FileWithIndex truth
        FileWithIndex query
        String output_name
    }

    command <<<
        hap.py -f "~{confident_bed}" -o "~{output_name}" -r "~{reference_genome.file}" "~{
            truth.file}" "~{query.file}"
    >>>

    output {
        VcfCompareOutput result = VcfCompareOutput {
            summary: "~{output_name}/summary.tsv",
            truth: "~{output_name}/truth.vcf.gz",
            query: "~{output_name}/query.vcf.gz",
        }
    }

    requirements {
        container: "quay.io/biocontainers/hap.py:0.3.15--py27hcb73b3d_0"
        cpu: 1
    }
}

task merge {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Run vkd merge on multiple query file and labeled query file."
        outputs: {
            dataframe: {
                help: "A parquet file with all input data merge",
            },
        }
    }

    parameter_meta {
        query: {
            help: "List of vcf query file.",
        }
        query_label: {
            help: "List of vcf query file with label.",
        }
        dataset: {
            help: "List of name associate to vcf query.",
        }
        output_name: {
            help: "Filename of output.",
        }
        clinvar: {
            help: "Clinvar annotation vcf file",
        }
        snpeff: {
            help: "Result of snpeff annotation of query vcf",
        }
        vep: {
            help: "Result of vep annotation of query vcf",
        }
    }

    input {
        Array[File] query
        Array[File] query_label
        Array[String] dataset
        String output_name
        File? clinvar
        Array[File]? snpeff
        Array[File]? vep
    }

    String clinvar_path = if defined(clinvar) then "-c " + select_first([
        clinvar,
    ]) else ""

    String snpeff_str = if defined(snpeff) then "-s " + sep(" ", select_first([
        snpeff,
    ])) else ""
    String vep_str = if defined(vep) then "-v " + sep(" ", select_first([
        vep,
    ])) else ""

    command <<<
        # shellcheck disable=SC2086
        # string are build by task
        vkd --threads 8 merge -n ~{sep(" ", dataset)} -q ~{sep(" ", query)} -Q ~{sep(" ", query_label
             )} ~{clinvar_path} ~{snpeff_str} ~{vep_str} -o "~{output_name}.parquet"
    >>>

    output {
        File dataframe = output_name + ".parquet"
    }

    requirements {
        container: "vkd:latest"
        cpu: 8
    }
}
