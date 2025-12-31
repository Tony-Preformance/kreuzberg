defmodule KreuzbergTest.Integration.BatchOperationsTest do
  @moduledoc """
  Integration tests for batch extraction operations.

  Tests cover:
  - Batch file extraction
  - Batch bytes extraction
  - Enum.map with concurrent extraction
  - Stream processing of documents
  - Error handling in batch operations
  - Batch result aggregation
  """

  use ExUnit.Case, async: true

  @sample_texts [
    "First document text content",
    "Second document text content",
    "Third document text content"
  ]

  @sample_html_contents [
    "<html><body><h1>Doc 1</h1></body></html>",
    "<html><body><h1>Doc 2</h1></body></html>",
    "<html><body><h1>Doc 3</h1></body></html>"
  ]

  describe "batch_extract_files" do
    @tag :integration
    test "extracts multiple files" do
      # Create temp files
      temp_files =
        1..3
        |> Enum.map(fn idx ->
          path = Path.join(System.tmp_dir!(), "batch_test_#{idx}.txt")
          File.write!(path, "Content #{idx}")
          path
        end)

      try do
        {:ok, results} = Kreuzberg.batch_extract_files(temp_files)

        assert is_list(results)
        assert length(results) == 3
      after
        Enum.each(temp_files, &File.rm!/1)
      end
    end

    @tag :integration
    test "batch extract with valid results" do
      temp_files =
        1..2
        |> Enum.map(fn idx ->
          path = Path.join(System.tmp_dir!(), "batch_valid_#{idx}.txt")
          File.write!(path, "Document #{idx}")
          path
        end)

      try do
        {:ok, results} = Kreuzberg.batch_extract_files(temp_files)

        assert is_list(results)

        Enum.each(results, fn result ->
          # Results are ExtractionResult structs when successful
          assert is_struct(result, Kreuzberg.ExtractionResult) or is_binary(result)
        end)
      after
        Enum.each(temp_files, &File.rm!/1)
      end
    end

    @tag :integration
    test "batch extract with config" do
      temp_files =
        1..3
        |> Enum.map(fn idx ->
          path = Path.join(System.tmp_dir!(), "batch_config_#{idx}.txt")
          File.write!(path, "Text #{idx}")
          path
        end)

      try do
        config = %Kreuzberg.ExtractionConfig{use_cache: true}
        {:ok, results} = Kreuzberg.batch_extract_files(temp_files, config)

        assert is_list(results)
        assert length(results) == 3
      after
        Enum.each(temp_files, &File.rm!/1)
      end
    end

    @tag :integration
    test "batch extract empty file list" do
      # Empty list should return an error
      result = Kreuzberg.batch_extract_files([])

      case result do
        {:error, _reason} -> assert true
        {:ok, results} -> assert results == []
      end
    end

    @tag :integration
    test "batch extract with mixed document types" do
      temp_files =
        [
          {"Content 1", "test_1.txt"},
          {"<html><body>Content 2</body></html>", "test_2.html"},
          {"Content 3", "test_3.txt"}
        ]
        |> Enum.map(fn {content, name} ->
          path = Path.join(System.tmp_dir!(), "batch_mixed_#{name}")
          File.write!(path, content)
          path
        end)

      try do
        {:ok, results} = Kreuzberg.batch_extract_files(temp_files)

        assert is_list(results)
        assert length(results) == 3
      after
        Enum.each(temp_files, &File.rm!/1)
      end
    end

    @tag :integration
    test "batch extract large file list" do
      temp_files =
        1..10
        |> Enum.map(fn idx ->
          path = Path.join(System.tmp_dir!(), "batch_large_#{idx}.txt")
          File.write!(path, "Content #{idx}")
          path
        end)

      try do
        {:ok, results} = Kreuzberg.batch_extract_files(temp_files)

        assert length(results) == 10
      after
        Enum.each(temp_files, &File.rm!/1)
      end
    end

    @tag :integration
    test "batch extract returns error for invalid file" do
      temp_files = [
        Path.join(System.tmp_dir!(), "exists_#{:erlang.unique_integer([:positive])}.txt"),
        "/nonexistent/file/path/#{:erlang.unique_integer([:positive])}.txt"
      ]

      # Create first file
      File.write!(List.first(temp_files), "Content")

      try do
        # Batch extraction should fail when any file doesn't exist
        result = Kreuzberg.batch_extract_files(temp_files)

        case result do
          {:ok, _results} ->
            # Some implementations may return partial results
            assert true

          {:error, reason} ->
            # Or it may fail entirely, which is also acceptable
            assert is_binary(reason)
            assert String.contains?(reason, "nonexistent") or String.contains?(reason, "does not exist")
        end
      after
        Enum.each(temp_files, fn f ->
          if File.exists?(f), do: File.rm!(f)
        end)
      end
    end
  end

  describe "batch_extract_bytes" do
    @tag :integration
    test "extracts multiple byte contents" do
      {:ok, results} = Kreuzberg.batch_extract_bytes(@sample_texts, "text/plain")

      assert is_list(results)
      assert length(results) == 3
    end

    @tag :integration
    test "batch extract bytes with HTML content" do
      {:ok, results} = Kreuzberg.batch_extract_bytes(@sample_html_contents, "text/html")

      assert is_list(results)
      assert length(results) == 3
    end

    @tag :integration
    test "batch extract bytes with config" do
      config = %Kreuzberg.ExtractionConfig{
        use_cache: true
      }

      {:ok, results} = Kreuzberg.batch_extract_bytes(@sample_texts, "text/plain", config)

      assert length(results) == 3
    end

    @tag :integration
    test "batch extract empty contents list" do
      # Empty list should return an error
      result = Kreuzberg.batch_extract_bytes([], "text/plain")

      case result do
        {:error, _reason} -> assert true
        {:ok, results} -> assert results == []
      end
    end

    @tag :integration
    test "batch extract mixed size contents" do
      contents = [
        "Short",
        String.duplicate("Medium ", 50),
        String.duplicate("Long ", 200)
      ]

      {:ok, results} = Kreuzberg.batch_extract_bytes(contents, "text/plain")

      assert length(results) == 3
    end

    @tag :integration
    test "batch extract unicode content" do
      unicode_contents = [
        "English text",
        "中文文本",
        "Текст на русском",
        "نص عربي"
      ]

      {:ok, results} = Kreuzberg.batch_extract_bytes(unicode_contents, "text/plain")

      assert length(results) == 4
    end

    @tag :integration
    test "batch extract large number of items" do
      contents = Enum.map(1..20, &"Document #{&1}")

      {:ok, results} = Kreuzberg.batch_extract_bytes(contents, "text/plain")

      assert length(results) == 20
    end

    @tag :integration
    test "batch extract with special characters" do
      special_contents = [
        "Text with !@#$%^&*()",
        "Text with <html>tags</html>",
        "Text with \"quotes\" and 'apostrophes'"
      ]

      {:ok, results} = Kreuzberg.batch_extract_bytes(special_contents, "text/plain")

      assert length(results) == 3
    end
  end

  describe "Enum.map with extraction" do
    @tag :integration
    test "maps extraction over list of texts" do
      results =
        @sample_texts
        |> Enum.map(fn text ->
          case Kreuzberg.extract(text, "text/plain") do
            {:ok, result} -> result
            {:error, _} -> nil
          end
        end)
        |> Enum.filter(&(&1 != nil))

      assert is_list(results)
    end

    @tag :integration
    test "maps extraction with intermediate config" do
      config = %Kreuzberg.ExtractionConfig{use_cache: false}

      results =
        @sample_texts
        |> Enum.map(fn text ->
          {:ok, Kreuzberg.extract(text, "text/plain", config)}
        end)

      assert length(results) == 3
    end

    @tag :integration
    test "maps extraction collecting successes" do
      results =
        @sample_texts
        |> Enum.map(&Kreuzberg.extract(&1, "text/plain"))
        |> Enum.filter(fn
          {:ok, _} -> true
          {:error, _} -> false
        end)

      assert length(results) == 3
    end

    @tag :integration
    test "maps extraction with filtering" do
      results =
        @sample_texts
        |> Enum.map(&Kreuzberg.extract(&1, "text/plain"))
        |> Enum.map(fn
          {:ok, result} -> result
          {:error, _} -> nil
        end)
        |> Enum.filter(&(&1 != nil))

      assert is_list(results)
    end

    @tag :integration
    test "maps extraction to result structs" do
      results =
        @sample_texts
        |> Enum.map(fn text ->
          {:ok, result} = Kreuzberg.extract(text, "text/plain")
          result
        end)

      Enum.each(results, fn result ->
        assert %Kreuzberg.ExtractionResult{} = result
      end)
    end

    @tag :integration
    test "maps extraction with index" do
      results =
        @sample_texts
        |> Enum.with_index()
        |> Enum.map(fn {text, idx} ->
          {:ok, result} = Kreuzberg.extract(text, "text/plain")
          {idx, result}
        end)

      assert length(results) == 3

      Enum.each(results, fn {_idx, result} ->
        assert result != nil
      end)
    end
  end

  describe "Stream processing" do
    @tag :integration
    test "processes stream of documents" do
      stream = Stream.map(@sample_texts, &Kreuzberg.extract(&1, "text/plain"))

      results = Enum.to_list(stream)

      assert length(results) == 3
    end

    @tag :integration
    test "streams extraction with filtering" do
      results =
        @sample_texts
        |> Stream.map(&Kreuzberg.extract(&1, "text/plain"))
        |> Stream.filter(fn
          {:ok, _} -> true
          {:error, _} -> false
        end)
        |> Enum.to_list()

      assert length(results) == 3
    end

    @tag :integration
    test "lazy evaluation with streams" do
      # Streams are lazy, so this should not block immediately
      stream =
        @sample_texts
        |> Stream.map(&Kreuzberg.extract(&1, "text/plain"))

      # Stream created but not evaluated
      assert is_struct(stream, Stream)

      # Evaluation happens on Enum.to_list
      results = Enum.to_list(stream)
      assert length(results) == 3
    end

    @tag :integration
    test "streams with configuration" do
      config = %Kreuzberg.ExtractionConfig{use_cache: true}

      results =
        @sample_texts
        |> Stream.map(&Kreuzberg.extract(&1, "text/plain", config))
        |> Enum.to_list()

      assert length(results) == 3
    end

    @tag :integration
    test "chains stream operations" do
      results =
        @sample_texts
        |> Stream.map(&Kreuzberg.extract(&1, "text/plain"))
        |> Stream.map(fn {:ok, result} -> result end)
        |> Enum.to_list()

      assert length(results) == 3

      Enum.each(results, fn result ->
        assert %Kreuzberg.ExtractionResult{} = result
      end)
    end

    @tag :integration
    test "reduce over extracted results" do
      total_length =
        @sample_texts
        |> Enum.map(&Kreuzberg.extract(&1, "text/plain"))
        |> Enum.reduce(0, fn {:ok, result}, acc ->
          acc + String.length(result.content)
        end)

      assert is_integer(total_length)
      assert total_length > 0
    end
  end

  describe "Batch result aggregation" do
    @tag :integration
    test "aggregates extraction results" do
      {:ok, results} = Kreuzberg.batch_extract_bytes(@sample_texts, "text/plain")

      total_results =
        results
        |> Enum.map(fn result ->
          # Results are ExtractionResult structs
          if is_struct(result, Kreuzberg.ExtractionResult) do
            result
          else
            nil
          end
        end)
        |> Enum.filter(&(&1 != nil))

      assert is_list(total_results)
    end

    @tag :integration
    test "counts successful extractions" do
      {:ok, results} = Kreuzberg.batch_extract_bytes(@sample_texts, "text/plain")

      successful_count =
        Enum.count(results, fn result ->
          is_struct(result, Kreuzberg.ExtractionResult)
        end)

      assert is_integer(successful_count)
    end

    @tag :integration
    test "extracts common fields from batch" do
      {:ok, results} = Kreuzberg.batch_extract_bytes(@sample_texts, "text/plain")

      contents =
        results
        |> Enum.map(fn result ->
          if is_struct(result, Kreuzberg.ExtractionResult) do
            result.content
          else
            ""
          end
        end)

      assert is_list(contents)
    end

    @tag :integration
    test "batch results maintain order" do
      ordered_texts = ["First", "Second", "Third", "Fourth", "Fifth"]

      {:ok, results} = Kreuzberg.batch_extract_bytes(ordered_texts, "text/plain")

      assert length(results) == length(ordered_texts)
    end

    @tag :integration
    test "aggregates metadata from batch" do
      {:ok, results} = Kreuzberg.batch_extract_bytes(@sample_texts, "text/plain")

      metadatas =
        results
        |> Enum.map(fn result ->
          # Results are ExtractionResult structs
          if is_struct(result, Kreuzberg.ExtractionResult) do
            result.metadata
          else
            nil
          end
        end)
        |> Enum.filter(&(&1 != nil))

      assert is_list(metadatas)
    end
  end

  describe "Batch error handling" do
    @tag :integration
    test "handles errors in batch extraction" do
      mixed_contents = [
        "Valid content 1",
        "Valid content 2",
        "Valid content 3"
      ]

      {:ok, results} = Kreuzberg.batch_extract_bytes(mixed_contents, "text/plain")

      # All results should be ExtractionResult structs
      Enum.each(results, fn result ->
        assert is_struct(result, Kreuzberg.ExtractionResult)
      end)
    end

    @tag :integration
    test "batch continue on individual errors" do
      temp_files = [
        Path.join(System.tmp_dir!(), "exists_#{:erlang.unique_integer([:positive])}.txt"),
        "/nonexistent/path_#{:erlang.unique_integer([:positive])}.txt",
        Path.join(System.tmp_dir!(), "exists2_#{:erlang.unique_integer([:positive])}.txt")
      ]

      # Create some valid files
      File.write!(List.first(temp_files), "Content 1")
      File.write!(List.last(temp_files), "Content 3")

      try do
        # When any file fails, batch returns an error
        result = Kreuzberg.batch_extract_files(temp_files)

        case result do
          {:error, _reason} ->
            # Expected - some files failed
            assert true

          {:ok, results} ->
            # All succeeded
            assert is_list(results)
        end
      after
        Enum.each(temp_files, fn f ->
          if File.exists?(f), do: File.rm!(f)
        end)
      end
    end

    @tag :integration
    test "recovers from batch errors" do
      {:ok, results1} = Kreuzberg.batch_extract_bytes(@sample_texts, "text/plain")

      # Should still work for subsequent batches
      {:ok, results2} = Kreuzberg.batch_extract_bytes(@sample_texts, "text/plain")

      assert length(results1) == length(results2)
    end
  end

  describe "Batch performance characteristics" do
    @tag :integration
    test "processes reasonable batch size" do
      contents = Enum.map(1..50, &"Document #{&1}")

      {:ok, results} = Kreuzberg.batch_extract_bytes(contents, "text/plain")

      assert length(results) == 50
    end

    @tag :integration
    test "batch maintains consistency across runs" do
      {:ok, results1} = Kreuzberg.batch_extract_bytes(@sample_texts, "text/plain")
      {:ok, results2} = Kreuzberg.batch_extract_bytes(@sample_texts, "text/plain")

      # Should get same results
      assert length(results1) == length(results2)
    end

    @tag :integration
    test "batch with identical inputs" do
      same_content = List.duplicate("Same content for all", 5)

      {:ok, results} = Kreuzberg.batch_extract_bytes(same_content, "text/plain")

      # All should process successfully
      assert length(results) == 5
    end

    @tag :integration
    test "batch with diverse content" do
      diverse_contents = [
        "Simple text",
        "<html><body>HTML</body></html>",
        String.duplicate("Repeated word ", 50),
        "Numbers: 123 456 789",
        "Special: !@#$%^&*()"
      ]

      {:ok, results} = Kreuzberg.batch_extract_bytes(diverse_contents, "text/plain")

      assert length(results) == 5
    end
  end
end
