version 1.2

import "../utils/types.wdl"

task variant {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Normalize variant in vcf file."
        outputs: {
            result: {
                help: "Normalized variant in vcf format with index associated.",
            },
        }
    }

    parameter_meta {
        vcf_path: {
            help: "Path of vcf.",
        }
        reference_path: {
            help: "Path to reference sequence.",
        }
    }

    input {
        File vcf_path
        File reference_path
    }

    String output_path = basename(vcf_path, ".vcf.gz") + ".norm.vcf.gz"

    command <<<
        bcftools norm --threads 4 -d all -m -any -c s -O z1 -W='tbi' -f "~{reference_path}" -o "~{
            output_path}" "~{vcf_path}"
    >>>

    output {
        FileWithIndex result = FileWithIndex {
            file: output_path,
            index: output_path + ".tbi",
        }
    }

    requirements {
        container: "quay.io/biocontainers/bcftools:1.22--h3a4d415_1"
        cpu: 4
    }
}
