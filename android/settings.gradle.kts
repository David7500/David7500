// Brez wrapperja: Gradle je orodje in zivi v ~/kajros-android/gradle-dist.
// Wrapper bi pomenil binarni .jar v gitu -- glej android/README.md.
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    // Odvisnosti sme dolocati SAMO ta datoteka. Ce jih kdaj kdo doda v modul,
    // naj gradnja pade, ne pa da tiho potegne se en repozitorij.
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "kajros"
include(":app")
