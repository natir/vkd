version 1.2

import "../utils/types.wdl"

task base {
  input {
    String uri
    String path
  }

  command <<<
    curl ~{uri} > ~{path}
  >>>

  output {
    File out_path = path
  }

  requirements {
    container: "richardjkendall/curl-bash"
  }
}

task vcf_with_index {
  input {
    String uri
    String path
  }

  command <<<
    curl ~{uri} > ~{path}
    curl ~{uri}.tbi > ~{path}.tbi
  >>>

  output {
    VcfWithIndex result = VcfWithIndex {
      vcf: path,
      tbi: path+".tbi"
    }
  }

  requirements {
    container: "richardjkendall/curl-bash"
  }
}
