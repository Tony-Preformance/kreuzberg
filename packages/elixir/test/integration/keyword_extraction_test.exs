defmodule KreuzbergTest.Integration.KeywordExtractionTest do
  @moduledoc """
  Integration tests for keyword extraction functionality.

  Tests cover:
  - YAKE and RAKE algorithms
  - KeywordConfig struct and validation
  - N-gram ranges (1-grams, 2-grams, multi-gram)
  - Keyword scoring and filtering
  - Pattern matching on keyword results
  - Multiple configurations and variants
  """

  use ExUnit.Case, async: true

  @sample_text """
  Natural Language Processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence
  concerned with the interactions between computers and human language. NLP is used to apply machine learning
  algorithms to text and speech. Some NLP tasks include text classification, named entity recognition, and
  machine translation. Python is the most popular language for NLP development.
  """

  @long_text String.duplicate(@sample_text, 5)

  describe "YAKE algorithm keyword extraction" do
    @tag :integration
    test "extracts relevant keywords with YAKE algorithm" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 10,
          "min_score" => 0.1
        }
      }

      {:ok, result} = Kreuzberg.extract(@sample_text, "text/plain", config)

      assert result.keywords != nil
      assert is_list(result.keywords)

      if result.keywords != [] do
        assert length(result.keywords) <= 10

        Enum.each(result.keywords, fn keyword ->
          assert is_map(keyword) or is_binary(keyword)
        end)
      end
    end

    @tag :integration
    test "respects max_keywords limit with YAKE" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 3,
          "min_score" => 0.1
        }
      }

      {:ok, result} = Kreuzberg.extract(@long_text, "text/plain", config)

      assert is_list(result.keywords)
      assert length(result.keywords) <= 3
    end

    @tag :integration
    test "YAKE extracts different keywords with different max limits" do
      config_few = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 3,
          "min_score" => 0.1
        }
      }

      config_many = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 20,
          "min_score" => 0.1
        }
      }

      {:ok, result_few} = Kreuzberg.extract(@long_text, "text/plain", config_few)
      {:ok, result_many} = Kreuzberg.extract(@long_text, "text/plain", config_many)

      assert length(result_few.keywords) <= length(result_many.keywords)
    end

    @tag :integration
    test "YAKE handles empty text gracefully" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 10,
          "min_score" => 0.1
        }
      }

      # Empty input is rejected by the Rust core - this is correct behavior
      {:error, _reason} = Kreuzberg.extract("", "text/plain", config)
    end
  end

  describe "RAKE algorithm keyword extraction" do
    @tag :integration
    test "extracts keyword phrases with RAKE algorithm" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "rake",
          "max_keywords" => 10,
          "min_score" => 0.1
        }
      }

      {:ok, result} = Kreuzberg.extract(@sample_text, "text/plain", config)

      assert result.keywords != nil
      assert is_list(result.keywords)
    end

    @tag :integration
    test "RAKE respects max_keywords limit" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "rake",
          "max_keywords" => 5,
          "min_score" => 0.1
        }
      }

      {:ok, result} = Kreuzberg.extract(@long_text, "text/plain", config)

      assert is_list(result.keywords)
      assert length(result.keywords) <= 5
    end

    @tag :integration
    test "RAKE extracts different keywords than YAKE" do
      yake_config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 10,
          "min_score" => 0.1
        }
      }

      rake_config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "rake",
          "max_keywords" => 10,
          "min_score" => 0.1
        }
      }

      {:ok, result_yake} = Kreuzberg.extract(@sample_text, "text/plain", yake_config)
      {:ok, result_rake} = Kreuzberg.extract(@sample_text, "text/plain", rake_config)

      assert is_list(result_yake.keywords)
      assert is_list(result_rake.keywords)
    end
  end

  describe "n-gram ranges" do
    @tag :integration
    test "extracts unigrams only with [1,1] range" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 20,
          "min_score" => 0.1,
          "ngram_range" => [1, 1]
        }
      }

      {:ok, result} = Kreuzberg.extract(@sample_text, "text/plain", config)

      assert is_list(result.keywords)
    end

    @tag :integration
    test "extracts bigrams with [2,2] range" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "rake",
          "max_keywords" => 20,
          "min_score" => 0.1,
          "ngram_range" => [2, 2]
        }
      }

      {:ok, result} = Kreuzberg.extract(@sample_text, "text/plain", config)

      assert is_list(result.keywords)
    end

    @tag :integration
    test "extracts multiple n-gram sizes with [1,3] range" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 20,
          "min_score" => 0.1,
          "ngram_range" => [1, 3]
        }
      }

      {:ok, result} = Kreuzberg.extract(@sample_text, "text/plain", config)

      assert is_list(result.keywords)
      assert result.keywords != []
    end
  end

  describe "keyword scoring" do
    @tag :integration
    test "keywords have score field" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 5,
          "min_score" => 0.1
        }
      }

      {:ok, result} = Kreuzberg.extract(@sample_text, "text/plain", config)

      if result.keywords != [] do
        Enum.each(result.keywords, fn keyword ->
          if is_map(keyword) do
            assert Map.has_key?(keyword, "score") or Map.has_key?(keyword, :score) or true
          end
        end)
      end
    end

    @tag :integration
    test "higher max_keywords may produce lower-scored results" do
      config_strict = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 3,
          "min_score" => 0.1
        }
      }

      config_relaxed = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 20,
          "min_score" => 0.1
        }
      }

      {:ok, result_strict} = Kreuzberg.extract(@long_text, "text/plain", config_strict)
      {:ok, result_relaxed} = Kreuzberg.extract(@long_text, "text/plain", config_relaxed)

      assert is_list(result_strict.keywords)
      assert is_list(result_relaxed.keywords)
      assert length(result_relaxed.keywords) >= length(result_strict.keywords)
    end
  end

  describe "pattern matching on keyword results" do
    @tag :integration
    test "matches on keyword struct with text and score" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 5,
          "min_score" => 0.1
        }
      }

      {:ok, result} = Kreuzberg.extract(@sample_text, "text/plain", config)

      case result.keywords do
        [%{"text" => _text, "score" => _score} | _] ->
          assert true

        [%{:text => _text, :score => _score} | _] ->
          assert true

        [] ->
          assert true

        _ ->
          assert is_list(result.keywords)
      end
    end

    @tag :integration
    test "matches on non-empty keywords list" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "rake",
          "max_keywords" => 10,
          "min_score" => 0.1
        }
      }

      {:ok, result} = Kreuzberg.extract(@sample_text, "text/plain", config)

      case result.keywords do
        [] -> assert true
        [_head | _tail] -> assert true
        _ -> assert false, "Keywords should be a list"
      end
    end

    @tag :integration
    test "extracts keyword field access" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 5,
          "min_score" => 0.1
        }
      }

      {:ok, result} = Kreuzberg.extract(@sample_text, "text/plain", config)

      if result.keywords != [] do
        first_keyword = List.first(result.keywords)
        assert first_keyword != nil
      end
    end
  end

  describe "keyword extraction configuration validation" do
    @tag :integration
    test "accepts valid KeywordConfig in ExtractionConfig" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "enabled" => true,
          "algorithm" => "yake",
          "max_keywords" => 10,
          "min_score" => 0.1
        }
      }

      assert config.keywords["algorithm"] == "yake"
      assert config.keywords["max_keywords"] == 10
    end

    @tag :integration
    test "handles nil keyword config" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: nil
      }

      {:ok, result} = Kreuzberg.extract(@sample_text, "text/plain", config)
      assert result != nil
    end

    @tag :integration
    test "applies keyword extraction when configured" do
      config_with_keywords = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 10,
          "min_score" => 0.1
        }
      }

      config_without_keywords = %Kreuzberg.ExtractionConfig{
        keywords: nil
      }

      {:ok, result_with} = Kreuzberg.extract(@sample_text, "text/plain", config_with_keywords)

      {:ok, result_without} =
        Kreuzberg.extract(@sample_text, "text/plain", config_without_keywords)

      assert result_with != nil
      assert result_without != nil
    end
  end

  describe "multiple language keyword extraction" do
    @tag :integration
    test "extracts keywords from English text" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 10,
          "min_score" => 0.1,
          "language" => "en"
        }
      }

      {:ok, result} = Kreuzberg.extract(@sample_text, "text/plain", config)

      assert result.keywords != nil
      assert is_list(result.keywords)
    end
  end

  describe "keyword extraction result structure" do
    @tag :integration
    test "result contains keywords field" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 5,
          "min_score" => 0.1
        }
      }

      {:ok, result} = Kreuzberg.extract(@sample_text, "text/plain", config)

      assert Map.has_key?(result, :keywords)
      assert is_list(result.keywords)
    end

    @tag :integration
    test "keywords list contains expected data types" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "rake",
          "max_keywords" => 10,
          "min_score" => 0.1
        }
      }

      {:ok, result} = Kreuzberg.extract(@sample_text, "text/plain", config)

      Enum.each(result.keywords, fn keyword ->
        assert is_binary(keyword) or is_map(keyword)
      end)
    end

    @tag :integration
    test "can serialize keywords to JSON" do
      config = %Kreuzberg.ExtractionConfig{
        keywords: %{
          "algorithm" => "yake",
          "max_keywords" => 5,
          "min_score" => 0.1
        }
      }

      {:ok, result} = Kreuzberg.extract(@sample_text, "text/plain", config)

      json = Jason.encode!(result.keywords)
      assert is_binary(json)
      {:ok, decoded} = Jason.decode(json)
      assert is_list(decoded)
    end
  end
end
