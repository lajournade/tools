package lajournade;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

public class JavaParserMain {

    public static void main(String[] args) {
        try {
            if (args.length != 1) {
                System.err.println("Invalid number of arguments.");
                usage();
            }

            final Path targetDir = Paths.get(args[0]);
            final List<Path> files = JavaFiles.find(targetDir);
            System.out.println("Files found: " + files.size());
            final int nbTryCatchLines = JavaFiles.countTryCatchLines(files);
            System.out.println("Nb of try-catch lines: " + nbTryCatchLines);
        } catch (Exception e) {
            System.err.println(e);
        }
    }

    public static void usage() {
        System.out.println("JavaParserMain <directory>");
    }

}
