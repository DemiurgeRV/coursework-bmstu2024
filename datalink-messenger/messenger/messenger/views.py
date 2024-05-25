import random

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import requests as req
from concurrent import futures
import base64


executor = futures.ThreadPoolExecutor()


class DataLinkView(APIView):
    def post(self, request):
        data = request.data
        message = base64.b64decode(data['data'])
        # print(message)
        segment_id = data['segment_id']
        num_of_seg = data['number_of_segments']
        date_send = data['date_send']
        login = data['login']
        message_id = data['message_id']
        executor.submit(processing, message, segment_id, num_of_seg, date_send, login, message_id)
        return Response(status=status.HTTP_200_OK)


def processing(message, segment_id, num_of_seg, date_send, login, message_id):
    encoded = hamming_encode(message, 4)
    encoded = making_err(encoded)
    decoded, err = hamming_decode(encoded, 7)
    if random.random() < 0.02:
        return

    data = {
        'data': base64.b64encode(bytes.fromhex(hex(int(decoded, 2))[2:])).decode(),
        'segment_id': segment_id,
        'number_of_segments': num_of_seg,
        'date_send': date_send,
        'login': login,
        'message_id': message_id,
        'error': err
    }

    print(data)

    req.post('http://172.20.10.9:8000/api/v1/segment', json=data)


def hamming_encode(message, block_size):
    bit_message = str(bin(int.from_bytes(message, byteorder='big')))[2:]
    # print(bit_message)
    reverse_blocks = [bit_message[max(i-block_size, 0):i].zfill(block_size) for i in range(len(bit_message), 0, -block_size)]
    blocks = list(reversed(reverse_blocks))
    encoded = ''
    for block in blocks:
        info_bits = [i for i in block]
        inspect_bits1 = str(bin((int(info_bits[0]) + int(info_bits[1]) + int(info_bits[3])) % 2)[2:])
        inspect_bits2 = str(bin((int(info_bits[0]) + int(info_bits[2]) + int(info_bits[3])) % 2)[2:])
        inspect_bits3 = str(bin((int(info_bits[1]) + int(info_bits[2]) + int(info_bits[3])) % 2)[2:])
        encoded_block = [inspect_bits1, inspect_bits2, info_bits[0], inspect_bits3, info_bits[1], info_bits[2], info_bits[3]]
        encoded_block = ''.join(encoded_block)
        encoded = encoded + encoded_block
    # print(encoded)
    return encoded


def making_err(encoded):
    if random.random() < 0.1:
        num = random.randint(0, len(encoded) - 1)
        # print(num)
        # print(encoded[num])
        encoded = list(encoded)
        encoded[num] = '0' if encoded[num] == '1' else '1'
        encoded = ''.join(encoded)
        # print(encoded[num])
        # print(encoded)
    return encoded


def hamming_decode(encoded, block_size):
    reverse_blocks = [encoded[max(i - block_size, 0):i] for i in range(len(encoded), 0, -block_size)]
    blocks = list(reversed(reverse_blocks))
    result = ''
    count = 0
    for block in blocks:
        block = list(block)
        # print(block)
        inspect_bit1 = int((block[0]) != str(bin((int(block[2]) + int(block[4]) + int(block[6])) % 2)[2:])) # если новое значение совпадает со старым то 0
        inspect_bit2 = int((block[1]) != str(bin((int(block[2]) + int(block[5]) + int(block[6])) % 2)[2:]))
        inspect_bit3 = int((block[3]) != str(bin((int(block[4]) + int(block[5]) + int(block[6])) % 2)[2:]))
        err_pos = inspect_bit1 * 1 + inspect_bit2 * 2 + inspect_bit3 * 4 # поиск позиции ошибки (если все 0 то ошибки нет)
        # print(err_pos)
        if err_pos != 0:
            block[err_pos - 1] = '0' if block[err_pos - 1] == '1' else '1'
            count += 1
        decoded = [block[2], block[4], block[5], block[6]]
        decoded = ''.join(decoded)
        result = result + decoded
    err = True if count != 0 else False
    if result[0] == '0':
        # print(result[1:])
        return result[1:], err
    return result, err
