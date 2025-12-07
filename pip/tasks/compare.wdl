version 1.2

import "../utils/types.wdl"

task aardvark {
  input {
    VcfWithIndex truth
    VcfWithIndex query
    File confident_bed
    FastaWithIndex reference_genome
    String output_name
  }

  command <<<
    aardvark compare --threads 4 --reference ~{reference_genome.fasta} --truth-vcf ~{truth.vcf} --query-vcf ~{query.vcf} --regions ~{confident_bed} --output-dir ~{output_name}
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
    cpu: 8
  }
}

task happy {
  input {
    VcfWithIndex truth
    VcfWithIndex query
    File confident_bed
    FastaWithIndex reference_genome
    String output_name
  }

  command <<<
    hap.py -f ~{confident_bed} -o ~{output_name} -r ~{reference_genome.fasta} ~{truth.vcf} ~{query.vcf}
  >>>

  output {
    VcfCompareOutput result = VcfCompareOutput {
      summary: "~{output_name}/summary.tsv",
      truth: "~{output_name}/truth.vcf.gz",
      query: "~{output_name}/query.vcf.gz",
    }
  }

  requirements {
    container: "quay.io/biocontainers/hap.py:0.3.15--py27hcb73b3d_0"
    cpu: 1
  }
}

task merge {
    input {
        Array[File] query
        Array[File] query_label
        Array[String] version
        File? clinvar
        File? snpeff
        File? vep
    }

    String versions = sep(" ", prefix("-n ", version))
    String querys = sep(" ", prefix("-q ", query))
    String querys_label = sep(" ", prefix("-Q ", query_label))

    String clinvar_path = if defined(clinvar) then " -c "+select_first([clinvar]) else ""
    String snpeff_path = if defined(snpeff) then " -s "+select_first([snpeff]) else ""
    String vep_path = if defined(vep) then " -v "+select_first([vep]) else ""

    command <<<
        vkd --threads 8 merge ~{versions} ~{querys} ~{querys_label} ~{clinvar_path} ~{snpeff_path} ~{vep_path} -o merge.parquet
    >>>

    output {
        File dataframe = "merge.parquet"
    }

    requirements {
        container: "vkd/latest"
        cpu: 8
    }
}
