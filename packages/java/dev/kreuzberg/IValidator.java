package dev.kreuzberg;

/**
 * Bridge interface for the Validator plugin system.
 *
 * Implementations are wrapped by ValidatorBridge and exposed to the native
 * runtime through Panama FFM upcall stubs.
 */
public interface IValidator {

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
