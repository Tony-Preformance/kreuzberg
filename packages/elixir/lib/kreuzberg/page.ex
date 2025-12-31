defmodule Kreuzberg.Page do
  @moduledoc """
  Structure representing a single page extracted from a multi-page document.

  Contains page-specific content, dimensions, and metadata when page-level
  extraction is enabled.

  ## Fields

    * `:number` - Page number (1-indexed)
    * `:content` - Text content extracted from this page
    * `:width` - Page width in inches or centimeters
    * `:height` - Page height in inches or centimeters
    * `:index` - Zero-indexed page index (alternative to number)

  ## Examples

      iex> page = %Kreuzberg.Page{
      ...>   number: 1,
      ...>   content: "Page 1 content here",
      ...>   width: 8.5,
      ...>   height: 11.0
      ...> }
      iex> page.number
      1
      iex> page.content
      "Page 1 content here"
  """

  @type t :: %__MODULE__{
          number: integer() | nil,
          content: String.t() | nil,
          width: float() | nil,
          height: float() | nil,
          index: integer() | nil
        }

  defstruct [
    :number,
    :content,
    :width,
    :height,
    :index
  ]

  @doc """
  Creates a new Page struct with required number and content.

  ## Parameters

    * `number` - The page number (1-indexed)
    * `content` - The text content of the page
    * `opts` - Optional keyword list with:
      * `:width` - Page width
      * `:height` - Page height
      * `:index` - Zero-indexed page index

  ## Returns

  A `Page` struct with the provided number, content, and options.

  ## Examples

      iex> Kreuzberg.Page.new(1, "Page content")
      %Kreuzberg.Page{number: 1, content: "Page content"}

      iex> Kreuzberg.Page.new(
      ...>   2,
      ...>   "More content",
      ...>   width: 8.5,
      ...>   height: 11.0
      ...> )
      %Kreuzberg.Page{
        number: 2,
        content: "More content",
        width: 8.5,
        height: 11.0
      }
  """
  @spec new(integer(), String.t(), keyword()) :: t()
  def new(number, content, opts \\ []) when is_integer(number) and is_binary(content) do
    %__MODULE__{
      number: number,
      content: content,
      width: Keyword.get(opts, :width),
      height: Keyword.get(opts, :height),
      index: Keyword.get(opts, :index)
    }
  end

  @doc """
  Creates a Page struct from a map.

  Converts a plain map (typically from NIF/Rust) into a proper struct.

  ## Parameters

    * `data` - A map containing page fields

  ## Returns

  A `Page` struct with matching fields populated.

  ## Examples

      iex> page_map = %{
      ...>   "number" => 1,
      ...>   "content" => "Page text",
      ...>   "width" => 8.5
      ...> }
      iex> Kreuzberg.Page.from_map(page_map)
      %Kreuzberg.Page{
        number: 1,
        content: "Page text",
        width: 8.5
      }
  """
  @spec from_map(map()) :: t()
  def from_map(data) when is_map(data) do
    # Handle both "number" and "page_number" fields from Rust side
    page_number = data["page_number"] || data["number"]

    %__MODULE__{
      number: page_number,
      content: data["content"],
      width: data["width"],
      height: data["height"],
      index: data["index"]
    }
  end

  @doc """
  Converts a Page struct to a map.

  Useful for serialization and passing to external systems.

  ## Parameters

    * `page` - A `Page` struct

  ## Returns

  A map with string keys representing all fields.

  ## Examples

      iex> page = %Kreuzberg.Page{number: 1, content: "text", width: 8.5}
      iex> Kreuzberg.Page.to_map(page)
      %{
        "number" => 1,
        "content" => "text",
        "width" => 8.5,
        ...
      }
  """
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = page) do
    %{
      "number" => page.number,
      "content" => page.content,
      "width" => page.width,
      "height" => page.height,
      "index" => page.index
    }
  end

  @doc """
  Returns the page size as a {width, height} tuple.

  Useful for layout calculations and image sizing.

  ## Parameters

    * `page` - A `Page` struct

  ## Returns

  A tuple `{width, height}` or nil if dimensions not available.

  ## Examples

      iex> page = %Kreuzberg.Page{width: 8.5, height: 11.0}
      iex> Kreuzberg.Page.size(page)
      {8.5, 11.0}

      iex> page = %Kreuzberg.Page{number: 1}
      iex> Kreuzberg.Page.size(page)
      nil
  """
  @spec size(t()) :: {float(), float()} | nil
  def size(%__MODULE__{width: w, height: h}) when is_number(w) and is_number(h) do
    {w, h}
  end

  def size(_), do: nil
end
