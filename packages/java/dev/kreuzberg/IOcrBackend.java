package dev.kreuzberg;

import java.util.List;

/**
 * Bridge interface for the OcrBackend plugin system.
 *
 * Implementations are wrapped by OcrBackendBridge and exposed to the native
 * runtime through Panama FFM upcall stubs.
 */
public interface IOcrBackend {

    /** Plugin name (used for registry keying). */
    String name();

    /** Plugin version. */
    String version();

    /** Initialize the plugin. */
    default void initialize() throws Exception {}

    /** Shut down the plugin. */
    default void shutdown() throws Exception {}

/** supports_language. */    boolean supports_language(String lang) throws Exception;

/** supported_languages. */    List<String> supported_languages() throws Exception;

/** supports_table_detection. */    boolean supports_table_detection() throws Exception;

/** supports_document_processing. */    boolean supports_document_processing() throws Exception;
}
