version 1.2

task snpeff {
  input {
    File vcf
  }

  command <<<
    snpeff -h
  >>>

  output {
    File annotated = vcf+"annot"
  }

  requirements {
    container: "quay.io/biocontainers/snpeff:5.3.0a--hdfd78af_1"
    cpu: 4
  }
}

task vep {
  input {
    File vcf
  }

  command <<<
    vep -h
  >>>

  output {
    File annotated = vcf+"annot"
}

  requirements {
    container: "quay.io/biocontainers/vep:115.2--pl5321h2a3209d_1"
    cpu: 4
  }
}
