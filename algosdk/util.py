from . import constants
from . import encoding
import base64
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError


def microalgos_to_algos(microalgos):
    """
    Convert microalgos to algos.

    Args:
        microalgos (int): how many microalgos

    Returns:
        int or float: how many algos
    """
    return microalgos/constants.microalgos_to_algos_ratio


def algos_to_microalgos(algos):
    """
    Convert algos to microalgos.

    Args:
        algos (int or float): how many algos

    Returns:
        int: how many microalgos
    """
    return algos*constants.microalgos_to_algos_ratio


def sign_bytes(to_sign, private_key):
    """
    Sign arbitrary bytes.

    Args:
        to_sign (bytes): bytes to sign

    Returns:
        str: base64 signature
    """
    to_sign = constants.bytes_prefix + to_sign
    private_key = base64.b64decode(private_key)
    signing_key = SigningKey(private_key[:constants.signing_key_len_bytes])
    signed = signing_key.sign(to_sign)
    signature = base64.b64encode(signed.signature).decode()
    return signature


def verify_bytes(message, signature, public_key):
    """
    Verify the signature of a message.

    Args:
        message (bytes): message that was signed
        signature (str): base64 signature
        public_key (str): base32 address

    Returns:
        bool: whether or not the signature is valid
    """
    verify_key = VerifyKey(encoding.decode_address(public_key))
    prefixed_message = constants.bytes_prefix + message
    try:
        verify_key.verify(prefixed_message, base64.b64decode(signature))
        return True
    except BadSignatureError:
        return False