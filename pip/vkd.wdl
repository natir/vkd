version 1.2

import "tasks/compare_to_gold.wdl"
import "tasks/download.wdl"
import "tasks/normalize_variant.wdl"

task vcf_compare2parquet {
  input {
    VcfWithIndex truth
    VcfWithIndex query
    VcfCompareOutput result
    String version
  }

  command <<<
    vkd -s ~{result.summary} -t ~{truth.vcf} -T ~{result.truth} -q ~{query.vcf} -Q ~{result.query} -o ~{version}.parquet
  >>>

  output {
    File dataframe = "~{version}.parquet"
  }

  requirements {
    container: "vkd/latest"
    cpu: 4
  }
}

workflow vkd {
  input {
    String gold_std_vcf_uri
    String gold_std_bed_uri
    Map[String, String] query_vcf_uri
    String reference_uri
  }

  call download.vcf_with_index as dl_gstd { input:
    uri = gold_std_vcf_uri,
    path = "gold_std.vcf.gz"
  }

  call download.base as dl_gstd_bed { input:
    uri = gold_std_bed_uri,
    path = "gold_std.bed"
  }

  call download.base as dl_reference { input:
    uri = reference_uri,
    path = "reference.fasta.gz"
  }

  call normalize_variant.normalize_variant as gstd { input:
    vcf_path = dl_gstd.result.vcf,
    reference_path = dl_reference.out_path
  }

  scatter (dataset_path in as_pairs(query_vcf_uri)) {
    call download.vcf_with_index as dl_query { input:
      uri = dataset_path.right,
      path = dataset_path.left+".vcf.gz"
    }

    call normalize_variant.normalize_variant as query { input:
      vcf_path = dl_query.result.vcf,
      reference_path = dl_reference.out_path
    }

    call compare_to_gold.compare_to_gold {
      truth = gstd.result,
      query = query.result,
      confident_bed = dl_gstd_bed.out_path,
      reference_genome = dl_reference.out_path,
      output_name = dataset_path.left,
    }

    call vcf_compare2parquet { input:
      truth = gstd.result,
      query = query.result,
      result = compare_to_gold.result,
      version = dataset_path.left
    }
  }

  output {
    Array[File] summary = vcf_compare2parquet.dataframe
  }
}
