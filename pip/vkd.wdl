version 1.2

import "tasks/compare_to_gold.wdl"
import "tasks/download.wdl"
import "tasks/normalize_variant.wdl"

task vcf_compare2parquet {
  input {
    Array[File] truth
    Array[File] query
    Array[File] truth_label
    Array[File] query_label
    Array[String] version
  }

  String versions = sep(" ", prefix("-n ", version))
  String truths = sep(" ", prefix("-t ", truth))
  String querys = sep(" ", prefix("-q ", query))
  String truths_label = sep(" ", prefix("-T ", truth_label))
  String querys_label = sep(" ", prefix("-Q ", query_label))

  command <<<
    vkd --threads 8 merge ~{versions} ~{truths} ~{truths_label} ~{querys} ~{querys_label} -o merge.parquet
  >>>

  output {
    File dataframe = "merge.parquet"
  }

  requirements {
    container: "vkd/latest"
    cpu: 8
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

    String version_ = dataset_path.left
    File truth_vcf = gstd.result.vcf
    File query_vcf = query.result.vcf
    File query_vcf_label = compare_to_gold.result.truth
    File truth_vcf_label = compare_to_gold.result.query
  }

  call vcf_compare2parquet { input:
      truth = truth_vcf,
      query = query_vcf,
      truth_label = truth_vcf_label,
      query_label = query_vcf_label,
      version = version_,
    }

  output {
    File summary = vcf_compare2parquet.dataframe
  }
}
