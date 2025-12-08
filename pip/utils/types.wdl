version 1.2

struct VcfCompareOutput {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Combine output of vcf compare tools."
    }

    parameter_meta {
        summary: {
            help: "Path to summary file produce by compare tools.",
        }
        truth: {
            help: "Path to truth file produce by compare tools.",
        }
        query: {
            help: "Path to query file produce by compare tools.",
        }
    }

    File summary
    File truth
    File query
}

struct FileWithIndex {
    meta {
        author: [
            "Pierre Marijon <pierre@marijon.fr>",
        ]
        description: "Combine path of file and associate index."
    }

    parameter_meta {
        file: {
            help: "Path to file.",
        }
        index: {
            help: "Path to index file associate to file.",
        }
    }

    File file
    File index
}
