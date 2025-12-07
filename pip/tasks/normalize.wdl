version 1.2

import "../utils/types.wdl"

task variant {
  input {
    File vcf_path
    File reference_path
  }

  String output_path = basename(vcf_path, ".vcf.gz")+".norm.vcf.gz"

  command <<<
    bcftools norm --threads 4 -d all -m -any -c s -O z1 -W='tbi' -f ~{reference_path} -o ~{output_path} ~{vcf_path}
  >>>

  output {
    VcfWithIndex result = VcfWithIndex {
      vcf: output_path,
      tbi: output_path+".tbi"
}
  }

  requirements {
    container: "quay.io/biocontainers/bcftools:1.22--h3a4d415_1"
    cpu: 4
  }
}
