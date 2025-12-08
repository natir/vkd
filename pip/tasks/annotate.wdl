version 1.2

task snpeff {
  input {
    File vcf
    String dataset_name
  }

  command <<<
    snpEff -Xms512m -Xmx8g ann -noStats hg38 ~{vcf} | gzip -1 - > ~{dataset_name}_snpeff.vcf.gz
  >>>

  output {
    File annotated = dataset_name+"_snpeff.vcf.gz"
  }

  requirements {
    container: "quay.io/biocontainers/snpeff:5.3.0a--hdfd78af_1"
    cpu: 1
  }
}

task vep {
  input {
    File vcf
    String dataset_name
  }

  command <<<
    vep -i ~{vcf} --fork 4 --vcf --vcf_info_field ANN --cache --species homo_sapiens --compress_output gzip -o ~{dataset_name}_vep.vcf.gz
  >>>

  output {
    File annotated = dataset_name+"_vep.vcf.gz"
  }

  requirements {
    container: "vep"
    cpu: 4
  }
}
