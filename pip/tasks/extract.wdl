version 1.2

import "../utils/types.wdl"

task chromosome {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Compare multiple vcf against gold standard and generate a dataframe to resume information."
        outputs: {
            result: {
                help: "Path where variant of a specific chromosome are store.",
            },
        }
    }

    parameter_meta {
        variant: {
            help: "File store information about variant.",
        }
        target_chromosome: {
            help: "Target chromosome.",
        }
    }

    input {
        FileWithIndex variant
        String target_chromosome
    }

    command <<<
        tabix -h -@ 4 "~{variant.file}" "~{target_chromosome}" | bgzip -c -l 1 - > "~{
            target_chromosome}.vcf.gz"
        tabix -@ 4 -p vcf "~{target_chromosome}.vcf.gz"
    >>>

    output {
        FileWithIndex result = FileWithIndex {
            file: target_chromosome + ".vcf.gz",
            index: target_chromosome + ".vcf.gz.tbi",
        }
    }

    requirements {
        container: "quay.io/biocontainers/htslib:1.22.1--h566b1c6_0"
        cpu: 4
    }
}
