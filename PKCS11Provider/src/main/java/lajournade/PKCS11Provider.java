package lajournade;

import java.io.FileOutputStream;
import java.security.Provider;
import java.security.Security;
import java.security.KeyStore;
import java.security.KeyPairGenerator;
import java.security.KeyPair;
import java.security.PublicKey;
import java.security.PrivateKey;

public class PKCS11Provider {

    public static void main(String[] args) {
        try {
            // Init PKCS11 provider
            final String configName = "/opt/pkcs11.cfg";
            final Provider provider = Security.getProvider("SunPKCS11").configure(configName);;
            System.out.println(provider.getInfo());

            // Log-in HSM
            final char[] pin = "1234".toCharArray();
            final KeyStore keyStore = KeyStore.getInstance("PKCS11", provider);
            keyStore.load(null, pin);

            // Generate keys
            final KeyPairGenerator keyPairGen = KeyPairGenerator.getInstance("RSA", provider);
            keyPairGen.initialize(4096);

            final KeyPair keyPair = keyPairGen.generateKeyPair();
            final PublicKey publicKey = keyPair.getPublic();
            final PrivateKey privateKey = keyPair.getPrivate();

            // Write public key (Private key value is private)
            try (FileOutputStream fos = new FileOutputStream("pubkey.der")) {
                fos.write(publicKey.getEncoded());
            }

            System.out.println("Key(s) saved on disk.");
        } catch (Exception e) {
            e.printStackTrace();
        }

    }
}