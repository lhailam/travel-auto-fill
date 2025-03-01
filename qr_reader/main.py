from qreader import QReader
import cv2


# Create a QReader instance
qreader = QReader()
def qr_code_reader(path):
    """
    Function to read the QR code from the image
    :param path: str: Path to the image file
    :return: str: Decoded QR data
    """
    image = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)

    # Use the detect_and_decode function to get the decoded QR data
    decoded_text = qreader.detect_and_decode(image=image)
    return decoded_text

qr_code_reader("images\\test1.jpg")