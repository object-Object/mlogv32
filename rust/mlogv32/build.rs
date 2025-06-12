use std::{env, error::Error, fs, path::PathBuf};

fn main() -> Result<(), Box<dyn Error>> {
    // build directory for this crate
    let out_dir = PathBuf::from(env::var_os("OUT_DIR").unwrap());

    // extend the library search path
    println!("cargo:rustc-link-search={}", out_dir.display());

    // rerun this script if any of these files change
    println!("cargo:rerun-if-changed=build.rs");

    if env::var_os("CARGO_FEATURE_DEFAULT_MEMORY").is_some() {
        // put memory.x in the build directory
        fs::write(out_dir.join("memory.x"), include_bytes!("memory.x"))?;

        println!("cargo:rerun-if-changed=memory.x");
    }

    Ok(())
}
