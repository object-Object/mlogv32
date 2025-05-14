use std::{env, error::Error, fs, path::PathBuf};

fn main() -> Result<(), Box<dyn Error>> {
    // build directory for this crate
    let out_dir = PathBuf::from(env::var_os("OUT_DIR").unwrap());

    // put memory.x in the build directory
    fs::write(out_dir.join("link.x"), include_bytes!("link.x"))?;

    // extend the library search path
    println!("cargo:rustc-link-search={}", out_dir.display());

    // rerun this script if any of these files change
    println!("cargo:rerun-if-changed=link.x");
    println!("cargo:rerun-if-changed=build.rs");

    Ok(())
}
