import base64
import msgpack
from collections import OrderedDict
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from . import transaction, error, auction, constants


def msgpack_encode(obj):
    """
    Encode the object using canonical msgpack.

    Args:
        obj (Transaction, SignedTransaction, MultisigTransaction, Multisig,
            Bid, or SignedBid): object to be encoded

    Returns:
        str: msgpack encoded object

    Note:
        Canonical Msgpack: maps must contain keys in lexicographic order; maps
        must omit key-value pairs where the value is a zero-value; positive
        integer values must be encoded as "unsigned" in msgpack, regardless of
        whether the value space is semantically signed or unsigned; integer
        values must be represented in the shortest possible encoding; binary
        arrays must be represented using the "bin" format family (that is, use
        the most recent version of msgpack rather than the older msgpack
        version that had no "bin" family).
    """
    if not isinstance(obj, OrderedDict):
        obj = obj._dictify()
    od = OrderedDict()
    for key in obj:
        if obj[key]:
            od[key] = obj[key]
    return base64.b64encode(msgpack.packb(od, use_bin_type=True)).decode()


def msgpack_decode(enc):
    """
    Decode a msgpack encoded object from a string.

    Args:
        enc (str): string to be decoded

    Returns:
        Transaction, SignedTransaction, Multisig, Bid, or SignedBid:
            decoded object
    """
    decoded = msgpack.unpackb(base64.b64decode(enc), raw=False)
    if "type" in decoded:
        if decoded["type"] == "pay":
            return transaction.PaymentTxn._undictify(decoded)
        else:
            return transaction.KeyregTxn._undictify(decoded)
    if "msig" in decoded:
        return transaction.MultisigTransaction._undictify(decoded)
    if "txn" in decoded:
        return transaction.SignedTransaction._undictify(decoded)
    if "subsig" in decoded:
        return transaction.Multisig._undictify(decoded)
    if "t" in decoded:
        return auction.NoteField._undictify(decoded)
    if "bid" in decoded:
        return auction.SignedBid._undictify(decoded)
    if "auc" in decoded:
        return auction.Bid._undictify(decoded)


def is_valid_address(addr):
    """
    Check if the string address is a valid Algorand address.

    Args:
        addr (str): base32 address

    Returns:
        bool: whether or not the address is valid
    """
    if not isinstance(addr, str):
        return False
    if not len(_undo_padding(addr)) == constants.address_len:
        return False
    try:
        decoded = decode_address(addr)
        if isinstance(decoded, str):
            return False
        return True
    except:
        return False


def decode_address(addr):
    """
    Decode a string address into its address bytes and checksum.

    Args:
        addr (str): base32 address

    Returns:
        bytes: address decoded into bytes

    """
    if not addr:
        return addr
    if not len(addr) == constants.address_len:
        raise error.WrongKeyLengthError
    decoded = base64.b32decode(_correct_padding(addr))
    addr = decoded[:-constants.check_sum_len_bytes]
    expected_checksum = decoded[-constants.check_sum_len_bytes:]
    chksum = _checksum(addr)

    if chksum == expected_checksum:
        return addr
    else:
        raise error.WrongChecksumError


def encode_address(addr_bytes):
    """
    Encode a byte address into a string composed of the encoded bytes and the
    checksum.

    Args:
        addr_bytes (bytes): address in bytes

    Returns:
        str: base32 encoded address
    """
    if not addr_bytes:
        return addr_bytes
    if not len(addr_bytes) == constants.address_len_bytes:
        raise error.WrongKeyBytesLengthError
    chksum = _checksum(addr_bytes)
    addr = base64.b32encode(addr_bytes+chksum)
    return _undo_padding(addr.decode())


def _checksum(addr):
    """
    Compute the checksum of size checkSumLenBytes for the address.

    Args:
        addr (bytes): address in bytes

    Returns:
        bytes: checksum of the address
    """
    hash = hashes.Hash(hashes.SHA512_256(), default_backend())
    hash.update(addr)
    chksum = hash.finalize()[-constants.check_sum_len_bytes:]
    return chksum


def _correct_padding(a):
    if len(a) % 8 == 0:
        return a
    return a + "="*(8-len(a) % 8)


def _undo_padding(a):
    return a.strip("=")