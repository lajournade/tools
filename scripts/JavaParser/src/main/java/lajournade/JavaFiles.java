package lajournade;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Class used for every operation related to a java file.
 */
public class JavaFiles {

    private JavaFiles() {
        super();
    }

    public static List<Path> find(Path targetDir) throws IOException {
        final List<Path> files = new ArrayList<>();
        find(targetDir, files);
        return files;
    }

    private static void find(Path targetDir, List<Path> files) throws IOException {
        final List<Path> filesFound = Files.list(targetDir)
                .filter(f -> Files.isRegularFile(f))
                .filter(f -> f.getFileName().toString().toLowerCase().endsWith(".java"))
                .collect(Collectors.toList());
        files.addAll(filesFound);
        final List<Path> directoriesFound = Files.list(targetDir)
                .filter(f -> Files.isDirectory(f))
                .collect(Collectors.toList());
        for (Path d : directoriesFound) {
            find(d, files);
        }
    }

    public static int countTryCatchLines(List<Path> files) throws IOException {
        int nbTryCatchLines = 0;
        for (Path file : files) {
            boolean counting = false;
            boolean tryOpen = false;
            boolean catchOpen = false;
            for (String line : Files.readAllLines(file)) {
                if (line.contains("try")) {
                    tryOpen = true;
                    counting = true;
                }
                else if (tryOpen && line.contains("catch")) {
                    tryOpen = false;
                    catchOpen = true;
                }
                else if (catchOpen && line.contains("}")) {
                    catchOpen = false;
                    counting = false;
                    nbTryCatchLines++;
                }

                if (counting) {
                    nbTryCatchLines++;
                }
            }

        }
        return nbTryCatchLines;
    }
}
