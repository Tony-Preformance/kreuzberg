package dev.kreuzberg;

/**
 * Bridge interface for the PostProcessor plugin system.
 *
 * Implementations are wrapped by PostProcessorBridge and exposed to the native
 * runtime through Panama FFM upcall stubs.
 */
public interface IPostProcessor {

    /** Plugin name (used for registry keying). */
    String name();

    /** Plugin version. */
    String version();

    /** Initialize the plugin. */
    default void initialize() throws Exception {}

    /** Shut down the plugin. */
    default void shutdown() throws Exception {}

/** priority. */    int priority() throws Exception;
}
