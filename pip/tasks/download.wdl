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

task fasta_with_index {
  input {
    String uri
    String path
  }

  command <<<
    curl ~{uri} > ~{path}
    curl ~{uri}.fai > ~{path}.fai
  >>>

  output {
    FastaWithIndex result = FastaWithIndex {
      fasta: path,
      fai: path+".fai"
    }
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

task clinvar {
  input {
    String version
  }

  String uri = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/weekly/clinvar_"+version+".vcf.gz"
  String path = "clinvar.vcf.gz"

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
