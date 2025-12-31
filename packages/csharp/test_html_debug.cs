using System;
using Kreuzberg;

var htmlPath = "/Users/naamanhirschfeld/workspace/kreuzberg-dev/kreuzberg/test_documents/web/html.html";
var config = new ExtractionConfig
{
    HtmlOptions = new HtmlConversionOptions { ExtractMetadata = true }
};

var result = KreuzbergClient.ExtractFileSync(htmlPath, config);

Console.WriteLine($"Success: {result.Success}");
Console.WriteLine($"MimeType: {result.MimeType}");
Console.WriteLine($"FormatType: {result.Metadata.FormatType}");
Console.WriteLine($"Format.Type: {result.Metadata.Format.Type}");
Console.WriteLine($"Format.Html: {result.Metadata.Format.Html}");
Console.WriteLine($"Metadata JSON: {System.Text.Json.JsonSerializer.Serialize(result.Metadata)}");
