version 1.2

import "../utils/types.wdl"

task tabix {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Recompress in block gzip a file and index it with tabix."
        outputs: {
            result: {
                help: "Recompress file with associated index",
            },
        }
    }

    parameter_meta {
        path: {
            help: "File path should be recompress",
        }
        preset: {
            help: "Preset use by tabix.",
        }
    }

    input {
        File path
        String preset
    }

    command <<<
        zcat "~{path}" | grep -v "#" | sort -k1,1 -k4,4n -k5,5n -t$'\t' | bgzip -c -l 1 - > "~{
            basename(path)}"
        tabix -@ 4 -p "~{preset}" "~{basename(path)}"
    >>>

    output {
        FileWithIndex result = FileWithIndex {
            file: basename(path),
            index: basename(path) + ".tbi",
        }
    }

    requirements {
        container: "quay.io/biocontainers/htslib@sha256:ce6e2a2ffaf3:1.22.1--h566b1c6_0"
        cpu: 4
    }
}
