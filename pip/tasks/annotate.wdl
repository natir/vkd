version 1.2

task snpeff {
  input {
    File vcf
    String dataset_name
  }

  command <<<
    snpEff ann -noStats hg38 ~{vcf} > ~{dataset_name}_snpeff.vcf
  >>>

  output {
    File annotated = dataset_name+"_snpeff.vcf"
  }

  requirements {
    container: "quay.io/biocontainers/snpeff:5.3.0a--hdfd78af_1"
    cpu: 4
  }
}

task vep {
  input {
    File vcf
    String dataset_name
  }

  command <<<
    vep -i ~{vcf} --vcf --vcf_info_field ANN -o ~{dataset_name}_vep.vcf
  >>>

  output {
    File annotated = dataset_name+"_vep.vcf"
  }

  requirements {
    container: "quay.io/biocontainers/vep:115.2--pl5321h2a3209d_1"
    cpu: 4
  }
}
