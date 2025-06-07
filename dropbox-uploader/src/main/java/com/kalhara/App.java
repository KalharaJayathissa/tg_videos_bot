package com.kalhara;

import com.dropbox.core.DbxRequestConfig;
import com.dropbox.core.v2.DbxClientV2;
import com.dropbox.core.v2.files.WriteMode;
import com.dropbox.core.v2.files.FileMetadata;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

public class App {

    // Your Dropbox App key & secret
    private static final String APP_KEY = "1b2v9fu2sf04uds";
    private static final String APP_SECRET = "rhb4nsutuwv96c5";

    // Stored refresh token (from your JSON)
    private static final String REFRESH_TOKEN = "GrhBLLdSSQ0AAAAAAAAAAfn3MH_rKVVQIhhXU0r5BfC0KCW84e0A2gjrRA9abOvz";

    // Hold the current access token here
    private static String accessToken = "sl.u.AFxhEtK_pxIxYGlImhO_Ik2UcN4SwFT41e501IvUID9k-Mq8h0Dsn08rYrYyKNXo9MhJB61-K-CDowUyfmyZ7d704g6JbEOGKeG53pQ0CzaBBSpGB_wuB7FBVDwhgHa83sRmhRqELx-WvZbIxLzRKC01MkR9KYnG5HvEKvbUuewxGYe8xXMUqEPPRUYpvUYcxgf8VCZLcULXq1B3F83S3kcx_qzWwDsCVh-dNoxAuw3J_VH6xs9JNYKmpvMehXWYQeuVrEc7kGZ_KJbAlyJYaJPwDnB6YxyQl7VGqIyc8h6oyxj4nqnFWkJFrUYNoEWGnb1z-90gz11L8oMqONvSOPpWnGfyuWd-pMmNyQj98TcmtlDgd6LL_cSfVa-7DXYm0q7XRQb9FVPy3DwudMYrzllMhVvmDVC02ccfC8BHVQQgV6iu4l-Hd73P3QObNPiIb0I_AWpBxJLHj5Rg2pcHZDforEvC2IRJQov7W8-QE0Qet2eah6ExU4bE3MfJsr5Eh46uUFVCJe0pXaw8-w8RGclUJ2orSmeJgCzNs_OA03au5fey6HnZKGLn0OI0W8KulC2vwj5ib8Jtps0O0Jq9HdkSNJXP23Xxs4T_fpdCOAVoxN_BrkBwLcOiKX8DJ_99mGD0HlDeTGhzo3nP9NplOMyH2EEbbb26Q3K5XAgmAmGFdT-oCQX_-F1mUVOzADtbV7Eq_zo38JFEfUFUuaY7p35bxetv3wisg-buLXtsbMCjOME7opLZ4U_w78iuWfYSWqOfKm7fhKOGaHQeazfDd1XRN-k-BGsjOscPl6YA0K5eTzxJGJEInwrk7X2Y2_E0q5KDLnUCt6rC8IBVODDUNozhZqQA_SLyS_iXPitcV5g9PC3ds1Rv-WvN1LbjvNCvaoJ8RFQac0ztA9ohbRFmcanT9_ielbyD1BYyNkyonFK8xLGFpZvLJABqugP3VmpXD6f0vm-fJmGXv5_1LmGbvBOKnTwEFA2HcbouyVxbzWSsL0r4r31HPolFFmaiC3k1wjqJ6tZ3jrwtODyq2TiqF73xJPVKLHKBQPPazfkhBVvr0DyMXTmXTbcfj4-daDIIGO4FCY-FtU6v39y9hY8bdE8byltJtUq4X6JNU6-YL8LgTm3Fxhy5-21d41etnyLyjh3Rxpf9yMik-Yv6vQRIW7nNzEiWKc3bpgyBFibO6Ppv1Ymscvzqn1pkEbslBPJjT8vlPcmCiASM1NHh9lR-wbln627Gvym6c5tlqYKYTdIG_gzhA4U7v2pyGeBOwzt-ii6p83eu_P7uhGkjbuZwsH1R7LWJWIsfyrS6XzKV2klV9yJy0sixnLa4TdZAJu8Ms-vqa97mh0BOibd5IWbYrN05YaW1Nh251w5lFZQPQivR-TcGLf7ICoRYmstjvGXqnp4P_Z0zEV4ZOgDFmNz69sq7ys8zu_15iGTFzW3lcdR00OsS8p4N_8KBZG63qrVOJx4";

    // Store token expiration timestamp (epoch ms)
    private static long accessTokenExpiry = 0;

    public static void main(String[] args) {
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();

        scheduler.scheduleAtFixedRate(() -> {
            try {
                // Refresh access token if expired or near expiry (say 1 min before)
                if (System.currentTimeMillis() > accessTokenExpiry - 60_000) {
                    System.out.println("Refreshing access token...");
                    refreshAccessToken();
                }
                // Proceed to upload files
                uploadAll();
                System.out.println("Scheduled upload completed at: " + System.currentTimeMillis());
            } catch (Exception e) {
                System.err.println("Error during scheduled upload: " + e.getMessage());
                e.printStackTrace();
            }
        }, 0, 30, TimeUnit.MINUTES);
    }

    public static void refreshAccessToken() throws IOException {
        URI uri = URI.create("https://api.dropboxapi.com/oauth2/token");
        URL url = uri.toURL();
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);

        // Basic Auth Header with app key & secret
        String auth = APP_KEY + ":" + APP_SECRET;
        String encodedAuth = Base64.getEncoder().encodeToString(auth.getBytes(StandardCharsets.UTF_8));
        conn.setRequestProperty("Authorization", "Basic " + encodedAuth);
        conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");

        // POST body parameters
        String body = "grant_type=refresh_token&refresh_token=" + REFRESH_TOKEN;

        try (OutputStream os = conn.getOutputStream()) {
            os.write(body.getBytes(StandardCharsets.UTF_8));
            os.flush();
        }

        int responseCode = conn.getResponseCode();
        if (responseCode == 200) {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()))) {
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }

                // Parse JSON response using Gson
                JsonObject jsonObject = JsonParser.parseString(response.toString()).getAsJsonObject();
                accessToken = jsonObject.get("access_token").getAsString();
                int expiresIn = jsonObject.get("expires_in").getAsInt();

                // Set new expiry time (current time + expiresIn seconds)
                accessTokenExpiry = System.currentTimeMillis() + expiresIn * 1000L;

                System.out.println("Access token refreshed. Expires in " + expiresIn + " seconds.");
            }
        } else {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getErrorStream()))) {
                StringBuilder errorResponse = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    errorResponse.append(line);
                }
                throw new IOException("Failed to refresh token. HTTP " + responseCode + ": " + errorResponse.toString());
            }
        }
    }

    public static void uploadFileToDropbox(String localFilePath, String dropboxPath) {
        File file = new File(localFilePath);
        if (!file.exists()) {
            System.out.println("File does not exist: " + file.getAbsolutePath());
            return;
        } else {
            System.out.println("File exists: " + file.getAbsolutePath());
        }

        DbxRequestConfig config = DbxRequestConfig.newBuilder("dropbox/java-uploader").build();
        DbxClientV2 client = new DbxClientV2(config, accessToken);

        try (InputStream inputStream = new FileInputStream(localFilePath)) {
            FileMetadata metadata = client.files().uploadBuilder(dropboxPath)
                    .withMode(WriteMode.OVERWRITE)
                    .uploadAndFinish(inputStream);
            System.out.println("File uploaded successfully: " + metadata.getPathLower());
        } catch (Exception e) {
            System.err.println("Error uploading file: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public static void uploadAll() {
        String[] files = {
                "videos.json",
                "video_stats.json",
                "stickers.json",
                "valid_users.json",
                "add_valid_users.txt",
                "users_info.json"
        };

        for (String file : files) {
            String localFilePath = file;
            String dropboxPath = "/tg_bot_files/" + file;
            uploadFileToDropbox(localFilePath, dropboxPath);
        }

        System.out.println("Upload completed.");
        System.out.println("You can check the file at https://www.dropbox.com/home/tg_bot_files");
    }
}
