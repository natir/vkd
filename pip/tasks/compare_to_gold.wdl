version 1.2

import "../utils/types.wdl"

task compare_to_gold {
  input {
    VcfWithIndex truth
    VcfWithIndex query
    File confident_bed
    File reference_genome
    String output_name
  }

  command <<<
    aardvark compare --threads 4 --reference ~{reference_genome} --truth-vcf ~{truth.vcf} --query-vcf ~{query.vcf} --regions ~{confident_bed} --output-dir ~{output_name}
  >>>

  output {
    VcfCompareOutput result = VcfCompareOutput {
      summary: "~{output_name}/summary.tsv",
      truth: "~{output_name}/truth.vcf.gz",
      query: "~{output_name}/query.vcf.gz",
    }
  }

  requirements {
    container: "quay.io/biocontainers/aardvark:0.10.2--h4349ce8_0"
    cpu: 4
  }
}
