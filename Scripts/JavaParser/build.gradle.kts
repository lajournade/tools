plugins {
    id("java")
    application
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

tasks.withType<Jar> {
    manifest {
        attributes["Main-Class"] = "lajournade.JavaParserMain"
    }
}

tasks.test {
    useJUnitPlatform()
}