from web3 import Web3
from web3._utils.abi import get_abi_output_types
from web3._utils.contracts import encode_abi
from eth_utils import encode_hex, function_abi_to_4byte_selector, add_0x_prefix
from web3.types import HexBytes

encode_hex_fn_abi = lambda fn_abi: encode_hex(
    function_abi_to_4byte_selector(fn_abi)
)

# Define the Web3 provider
web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/bsc'))

# Define the multicall and nft contract address | all chains address on https://www.multicall3.com/
multicall_address = web3.to_checksum_address('0xcA11bde05977b3631167028862bE2a173976CA11')
# Define contract with function tokenOfOwnerByIndex
alien_nft_address = web3.to_checksum_address('0xF3857306a37264f15a19ad37DA8A9485e5f7CfB3')

# Define the ABI for the tokenOfOwnerByIndex function
TOKEN_OF_OWNER_BY_INDEX_ABI = {
    "constant": True,
    "inputs": [
        {"internalType": "address", "name": "owner", "type": "address"},
        {"internalType": "uint256", "name": "index", "type": "uint256"}
    ],
    "name": "tokenOfOwnerByIndex",
    "outputs": [
        {"internalType": "uint256", "name": "", "type": "uint256"}
    ],
    "stateMutability": "view",
    "type": "function"
}

# Define the selector for the tokenOfOwnerByIndex function
token_of_owner_by_index_selector = encode_hex(function_abi_to_4byte_selector(TOKEN_OF_OWNER_BY_INDEX_ABI))
# Define the output types for the multicall
token_of_owner_by_index_output_types = get_abi_output_types(TOKEN_OF_OWNER_BY_INDEX_ABI)

# ABI multicall contract
TRY_AGGREGATE_ABI = {"inputs": [{"name": "requireSuccess", "type": "bool"}, {
    "components": [{"name": "target", "type": "address"}, {"name": "callData", "type": "bytes"}], "name": "calls",
    "type": "tuple[]"}], "name": "tryAggregate", "outputs": [
    {"components": [{"name": "success", "type": "bool"}, {"name": "returnData", "type": "bytes"}], "name": "returnData",
     "type": "tuple[]"}], "stateMutability": "nonpayable", "type": "function"}
try_aggregate_selector = encode_hex_fn_abi(TRY_AGGREGATE_ABI)
try_aggregate_output_types = get_abi_output_types(TRY_AGGREGATE_ABI)


def multicall_token_of_owner_by_index(web3: Web3, multicall_address: str, owner_address: str, indices: range):
    # Encode the calls for each index
    encoded_calls = [
        (
            owner_address,
            index,
            encode_abi(
                web3,
                TOKEN_OF_OWNER_BY_INDEX_ABI,
                (owner_address, int(index)),
                token_of_owner_by_index_selector,
            ),
        )
        for index in indices
    ]

    # Encode the multicall data
    data = add_0x_prefix(encode_abi(
        web3,
        TRY_AGGREGATE_ABI,
        (False, [(alien_nft_address, call) for address, index, call in encoded_calls]),
        try_aggregate_selector
    ))
    tx_raw_data = web3.eth.call({"to": multicall_address, "data": data})

    output_data = web3.codec.decode(try_aggregate_output_types, tx_raw_data)[0]

    output_data = (
        #token_of_owner_by_index_output_types == ["uint256"]
        str(web3.codec.decode(token_of_owner_by_index_output_types, HexBytes(token_id))[0]) for (_, token_id) in output_data
    )

    return dict(zip(indices, output_data))


# Example usage
owner_address = web3.to_checksum_address('0xf3857306a37264f15a19ad37da8a9485e5f7cfb3')
indices = range(0,5)  # Adjust the range as needed

result = multicall_token_of_owner_by_index(web3, multicall_address, owner_address, indices)
print(result)

#example print: {0: '70925', 1: '684531', 2: '745704', 3: '699010', 4: '699011'} and etc
