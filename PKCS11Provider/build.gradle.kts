plugins {
    id("java")
}

group = "lajournade"
version = "1.0-SNAPSHOT"


repositories {
    mavenCentral()
}

dependencies {
    testImplementation(platform("org.junit:junit-bom:5.10.0"))
    testImplementation("org.junit.jupiter:junit-jupiter")
}
tasks.jar {
    manifest {
        attributes["Main-Class"] = "lajournade.PKCS11Provider"
    }
}

tasks.test {
    useJUnitPlatform()
}

dependencies {

}