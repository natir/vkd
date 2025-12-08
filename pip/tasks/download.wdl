version 1.2

import "../utils/types.wdl"

task base {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Download a file point by an uri with curl."
        outputs: {
            path: {
                help: "Path uri file content are write.",
            },
        }
    }

    parameter_meta {
        filename: {
            help: "filename where file will be write.",
        }
        uri: {
            help: "Uri to file.",
        }
    }

    input {
        File filename
        String uri
    }

    command <<<
        curl "~{uri}" > "~{filename}"
    >>>

    output {
        File path = filename
    }

    requirements {
        container: "richardjkendall/curl-bash@sha256:62f573d6dde0"
    }
}

task file_with_index {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Download a file with associated index."
        outputs: {
            result: {
                help: "Path of file and path of index associate",
            },
        }
    }

    parameter_meta {
        uri: {
            help: "Uri to file.",
        }
        filename: {
            help: "Filename where file will be write.",
        }
        index: {
            help: "Extension of index.",
        }
    }

    input {
        String uri
        String filename
        String index
    }

    command <<<
        curl "~{uri}" > "~{filename}"
        curl "~{uri}.~{index}" > "~{filename}.~{index}"
    >>>

    output {
        FileWithIndex result = FileWithIndex {
            file: filename,
            index: filename + index,
        }
    }

    requirements {
        container: "richardjkendall/curl-bash@sha256:62f573d6dde0"
    }
}

task clinvar {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Download a fasta file with associated fasta index."
        outputs: {
            result: {
                help: "Path of fasta file and path of index associate.",
            },
        }
    }

    parameter_meta {
        version: {
            help: "Version of clinvar.",
        }
    }

    input {
        String version
    }

    String uri = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/weekly/clinvar_" + version
        + ".vcf.gz"
    String path = "clinvar.vcf.gz"

    command <<<
        curl "~{uri}" > "~{path}"
        curl "~{uri}.tbi" > "~{path}.tbi"
    >>>

    output {
        FileWithIndex result = FileWithIndex {
            file: path,
            index: path + ".tbi",
        }
    }

    requirements {
        container: "richardjkendall/curl-bash@sha256:62f573d6dde0"
    }
}
