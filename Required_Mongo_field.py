import cloudinary
import cloudinary.api
import logging

from config import *
# Configure logging
logging.basicConfig(level=logging.INFO)



# Configure Cloudinary using credentials from config
cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=CLOUD_API_KEY,
    api_secret=CLOUD_API_SECRET
)


def fetch_image(public_id):
    try:
        # Generate the URL for the image
        url, options = cloudinary.utils.cloudinary_url(public_id, format='jpg')

        # Log the generated URL
        logging.info(f"Generated Cloudinary URL: {url}")

        # Try to fetch the image info to verify the connection
        image_info = cloudinary.api.resource(public_id)

        logging.info("Image fetched successfully!")
        logging.info(f"Image info: {image_info}")

        return url  # Return the URL for use if needed
    except cloudinary.exceptions.NotFound as e:
        logging.error(f"Image not found: {e}")
    except cloudinary.exceptions.Error as e:
        logging.error(f"Cloudinary error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

# Example usage
if __name__ == "__main__":
    public_id = "cloth_fkhgsr"  # Replace with your Cloudinary public ID
    image_url = fetch_image(public_id)

    if image_url:
        print(f"Image URL: {image_url}")
