version 1.2

import "../utils/types.wdl"

task snpeff {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Run snpeff annotation on a vcf call with hg38."
        outputs: {
            annotated: {
                help: "File with snpeff annotation.",
            },
        }
    }

    parameter_meta {
        vcf: {
            help: "The vcf file.",
        }
        dataset_name: {
            help: "Prefix of output file name.",
        }
    }

    input {
        File vcf
        String dataset_name
    }

    command <<<
        snpEff -Xms512m -Xmx8g ann -noStats hg38 "~{vcf}" | gzip -1 - > "~{dataset_name}_snpeff.vcf.gz"
    >>>

    output {
        File annotated = dataset_name + "_snpeff.vcf.gz"
    }

    requirements {
        container: "quay.io/biocontainers/snpeff@sha256:2a79bffc9c255c9a3b0503aab730ed3f428c40838a97be262cfd3b89d91fd9f3:5.3.0a--hdfd78af_1"
        cpu: 1
    }
}

task vep {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Run vep annotation on a vcf call with hg38."
        outputs: {
            annotated: {
                help: "File with snpeff annotation.",
            },
        }
    }

    parameter_meta {
        vcf: {
            help: "The vcf file.",
        }
        reference_genome: {
            help: "Path to reference genome associate with calling and annotation.",
        }
        gff: {
            help: "Gff3 compress in bgzip and index.",
        }
        dataset_name: {
            help: "Prefix of output file name.",
        }
    }

    input {
        File vcf
        File reference_genome
        FileWithIndex gff
        String dataset_name
    }

    command <<<
        mkdir -p /root/.vep/homo_sapiens/115
        vep -i "~{vcf}" --fork 4 --vcf --vcf_info_field ANN --cache --offline --gff "~{gff.file
            }" --fasta "~{reference_genome}" --compress_output gzip -o "~{dataset_name}_vep.vcf.gz"
    >>>

    output {
        File annotated = dataset_name + "_vep.vcf.gz"
    }

    requirements {
        container: "quay.io/biocontainers/ensembl-vep@sha256:04cbcc3c54350ebf51c02698dd23183b1b9db22daa9983037f7260ee37601aa7:115.2--pl5321h2a3209d_1"
        cpu: 4
    }
}
