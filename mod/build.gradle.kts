import com.xpdustry.toxopid.extension.anukeXpdustry
import com.xpdustry.toxopid.spec.ModMetadata
import com.xpdustry.toxopid.spec.ModPlatform

plugins {
    alias(libs.plugins.kotlin.jvm)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.indra.common)
    alias(libs.plugins.shadow)
    alias(libs.plugins.toxopid)
}

val metadata = ModMetadata.fromJson(file("mod.hjson"))
group = "gay.object"
version = metadata.version
description = metadata.description

toxopid {
    compileVersion = "v${metadata.minGameVersion}"
    platforms = setOf(ModPlatform.DESKTOP, ModPlatform.ANDROID, ModPlatform.SERVER)
}

repositories {
    mavenCentral()
    anukeXpdustry()
}

dependencies {
    compileOnly(toxopid.dependencies.arcCore)
    compileOnly(toxopid.dependencies.mindustryCore)

    implementation(libs.kotlin.stdlib)
    implementation(libs.kotlinx.coroutines)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.ktor.network)
}

indra {
    javaVersions {
        target(8)
        minimumToolchain(17)
    }
}

// FIXME: we should be using kotlin-runtime instead, but it doesn't seem to work on build 149

//configurations.runtimeClasspath {
//    exclude("org.jetbrains.kotlin")
//    exclude("org.jetbrains.kotlinx")
//}

tasks {
    val generateResources by registering {
        inputs.property("metadata", metadata)
        val output = temporaryDir.resolve("mod.json")
        outputs.file(output)
        doLast {
            output.writeText(ModMetadata.toJson(metadata, true))
        }
    }

    shadowJar {
        archiveClassifier = "mod"
        from(generateResources)
        from("./assets") {
            include("**")
        }
    }

    build {
        dependsOn(shadowJar)
    }
}
