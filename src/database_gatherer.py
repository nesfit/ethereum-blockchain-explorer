"""Gathers requested information from the database."""
# from multiprocessing import Lock
from typing import Any, List, Dict, Union
import logging

import src.coders.coder as coder

LOG = logging.getLogger()


class DatabaseGatherer:
    """Class that gathers the requested information from the database."""

    def __init__(self, db: Any) -> None:
        """
        Initialization.

        Args:
                db: Database instance.
        """
        self.db = db
        self.blocks_db = db.prefixed_db(b'block-')
        self.block_hash_db = db.prefixed_db(b'hash-block-')
        self.block_timestamp_db = db.prefixed_db(b'timestamp-block-')
        self.transaction_db = db.prefixed_db(b'transaction-')
        self.tx_hash_db = db.prefixed_db(b'tx-hash-')
        self.address_db = db.prefixed_db(b'address-')

    def get_block_by_hash(self, block_hash: str) -> Union[Dict[str, str], None]:
        """
        Retrieves block information specified by its hash.

        Args:
            block_hash: Block hash.

        Returns:
            Dictionary representing the blockchain block.
        """
        block_index = self.block_hash_db.get(block_hash.encode())
        if block_index is None:
            LOG.info('Block of specified hash not found.')
            return None

        raw_block = self.blocks_db.get(block_index)
        block = coder.decode_block(raw_block)
        transaction_range = block['transactionIndexRange'].split('-')
        del block['transactionIndexRange']
        transactions = []  # type: List[Dict[str, Any]]

        if transaction_range == ['']:
            block['transactions'] = transactions
            return block

        tx_start = int(transaction_range[0])
        tx_end = int(transaction_range[1])

        for i in range(tx_start, tx_end + 1):
            raw_tx = self.transaction_db.get(str(i).encode())
            if raw_tx is None:
                LOG.info('Record of block\'s transaction not found. Possible DB corruption.')
                return None
            transaction = coder.decode_transaction(raw_tx)
            transactions.append(transaction)
        block['transactions'] = transactions

        return block

    def get_block_index_by_hash(self, block_index: str) -> Union[str, None]:
        """
        Retrieves block hash by its index.

        Args:
            block_index: Index of a block.

        Returns:
            Block hash.
        """
        raw_block = self.blocks_db.get(block_index.encode())
        if raw_block is None:
            return None
        block = coder.decode_block(raw_block)
        return block['hash']

    def get_blocks_by_datetime(self, limit: int, block_start: int,
                               block_end: int) -> Union[List[Dict[str, Any]], None]:
        """
        Retrieves multiple blocks based on specified datetime range.

        Args:
            limit: Maximum blocks to gether.
            block_start: Beginning datetime.
            block_end: End datetime.

        Returns:
            List of block dictionaries.
        """
        block_indexes = []  # type: List[str]
        blocks = []  # type: List[Dict[str, Any]]
        counter = 0
        it = self.block_timestamp_db.iterator(start=str(block_start).encode(),
                                              stop=str(block_end).encode())
        for timestamp, block_index in it:
            if counter >= limit and limit != 0:
                break
            if int(block_index.decode()) >= block_start and int(block_index.decode()) <= block_end:
                block_indexes.append(int(block_index.decode()))
                counter += 1
        if block_indexes == []:
            return None

        # Since DB is working with string-numbers things might be kind of tricky
        block_indexes.sort()
        for i in range(block_indexes[0], block_indexes[-1] + 1):
            raw_block = self.blocks_db.get(str(i).encode())
            block = coder.decode_block(raw_block)
            transaction_range = block['transactionIndexRange'].split('-')
            del block['transactionIndexRange']
            transactions = []  # type: List[Dict[str, Any]]

            if transaction_range == ['']:
                block['transactions'] = transactions
                blocks.append(block)
                continue
            
            tx_start = int(transaction_range[0])
            tx_end = int(transaction_range[1])
            for j in range(tx_start, tx_end + 1):
                raw_tx = self.transaction_db.get(str(j).encode())
                if raw_tx is None:
                    LOG.info('Record of block\'s transaction not found. Possible DB corruption.')
                    return None
                transaction = coder.decode_transaction(raw_tx)
                transactions.append(transaction)
            block['transactions'] = transactions
            blocks.append(block)

        return blocks

    def get_blocks_by_indexes(self, index_start: str,
                              index_end: str) -> Union[List[Dict[str, Any]], None]:
        """
        Retrieves a list of blocks specified by an index range.

        Args:
            index_start: First index.
            index_end: Last index.

        Returns:
            A list of blocks.
        """
        blocks = []

        for i in range(int(index_start), int(index_end) + 1):
            raw_block = self.blocks_db.get(str(i).encode())
            block = coder.decode_block(raw_block)
            transaction_range = block['transactionIndexRange'].split('-')
            del block['transactionIndexRange']
            transactions = []  # type: List[Dict[str, Any]]

            if transaction_range == ['']:
                block['transactions'] = transactions
                blocks.append(block)
                continue
            
            tx_start = int(transaction_range[0])
            tx_end = int(transaction_range[1])
            for j in range(tx_start, tx_end + 1):
                raw_tx = self.transaction_db.get(str(j).encode())
                if raw_tx is None:
                    LOG.info('Record of block\'s transaction not found. Possible DB corruption.')
                    return None
                transaction = coder.decode_transaction(raw_tx)
                transactions.append(transaction)
            block['transactions'] = transactions
            blocks.append(block)

        return blocks

    def get_transaction_by_hash(self, tx_hash) -> Union[Dict[str, Any], None]:
        """
        Retrieves transaction specified by its hash.

        Args:
            tx_hash: Hash of the transaction.

        Returns:
            The desired transaction.
        """
        tx_index = self.tx_hash_db.get(tx_hash.encode()).decode()
        if tx_index is None:
            return None

        raw_tx = self.transaction_db(tx_index.encode())
        transaction = coder.decode_transaction(raw_tx)

        return transaction

    def get_transactions_of_block_by_hash(self,
                                          block_hash: str) -> Union[List[Dict[str, Any]], None]:
        """
        Gets list of transactions belonging to specified block.

        Args:
            block_hash: hash of the block.

        Returns:
            List of specified block transactions.
        """
        block_index = self.block_hash_db.get(block_hash.encode()).decode()
        if block_index is None:
            return None

        raw_block = self.blocks_db.get(block_index.encode())
        block = coder.decode_block(raw_block)
        transaction_range = block['transactionIndexRange'].split('-')
        transactions = []  # type: List[Dict[str, Any]]

        it = self.transaction_db.iterator(start=transaction_range[0].encode(),
                                          stop=transaction_range[0].encode(),
                                          include_key=False)
        for raw_tx in it:
            transactions.append(coder.decode_transaction(raw_tx))

        return transactions

    def get_transactions_of_block_by_index(self,
                                           block_index: str) -> Union[List[Dict[str, Any]], None]:
        """
        Gets list of transactions belonging to specified block.

        Args:
            block_index: index of the block.

        Returns:
            List of specified block transactions.
        """
        raw_block = self.blocks_db.get(block_index.encode())
        if raw_block is None:
            return None
        block = coder.decode_block(raw_block)
        transaction_range = block['transactionIndexRange'].split('-')
        transactions = []  # type: List[Dict[str, Any]]

        it = self.transaction_db.iterator(start=transaction_range[0].encode(),
                                          stop=transaction_range[0].encode(),
                                          include_key=False)
        for raw_tx in it:
            transactions.append(coder.decode_transaction(raw_tx))

        return transactions

    def get_transactions_of_address(self, addr: str, time_from: str, time_to: str,
                                    val_from: str,
                                    val_to: str) -> Union[List[Dict[str, Any]], None]:
        """
        Get transactions of specified address, with filtering by time and transferred capital.

        Args:
            addr: Ethereum address.
            time_from: Beginning datetime to take transactions from.
            time_to: Ending datetime to take transactions from.
            val_from: Minimum transferred currency of the transactions.
            val_to: Maximum transferred currency of transactions.

        Returns:
            List of address transactions.
        """
        # TODO OPTIONAL ARGUMENT WHAT VALUE???
        raw_address = self.address_db.get(addr.encode())
        if raw_address is None:
            return None
        address = coder.decode_address(raw_address)
        input_transactions = []
        output_transactions = []

        for transaction in address['inputTransactionIndexes'].split('|'):
            tx_index, timestamp, value = transaction.split('+')
            if (int(time_from) <= int(timestamp) and int(time_to) >= int(timestamp)
                    and int(val_from) <= int(value) and int(val_to) >= int(value)):
                raw_tx = self.transaction_db.get(tx_index.encode())
                input_transactions.append(coder.decode_transaction(raw_tx))

        for transaction in address['outputTransactionIndexes'].split('|'):
            tx_index, timestamp, value = transaction.split('+')
            if (int(time_from) <= int(timestamp) and int(time_to) >= int(timestamp)
                    and int(val_from) <= int(value) and int(val_to) >= int(value)):
                raw_tx = self.transaction_db.get(tx_index.encode())
                output_transactions.append(coder.decode_transaction(raw_tx))

        return input_transactions + output_transactions

    def get_address(self, addr: str, time_from: str, time_to: str,
                    val_from: str, val_to: str,
                    no_tx_list: str) -> Union[List[Dict[str, Any]], None]:
        """
        Get information of an address, with the possibility of filtering/limiting transactions.

        Args:
            addr: Ethereum address.
            time_from: Beginning datetime to take transactions from.
            time_to: Ending datetime to take transactions from.
            val_from: Minimum transferred currency of the transactions.
            val_to: Maximum transferred currency of transactions.
            no_tx_list: Maximum transactions to return

        Returns:
            Address information along with its transactions.
        """
        # TODO: tie pocty transakcii adresy by som asi nevracal...
        raw_address = self.address_db.get(addr.encode())
        if raw_address is None:
            return None
        address = coder.decode_address(raw_address)
        input_transactions = []
        output_transactions = []
        counter = 0

        for transaction in address['inputTransactionIndexes'].split('|'):
            tx_index, timestamp, value = transaction.split('+')
            if (int(time_from) <= int(timestamp) and int(time_to) >= int(timestamp)
                    and int(val_from) <= int(value) and int(val_to) >= int(value)):
                counter += 1
                if counter > int(no_tx_list):
                    break
                raw_tx = self.transaction_db.get(tx_index.encode())
                input_transactions.append(coder.decode_transaction(raw_tx))

        for transaction in address['outputTransactionIndexes'].split('|'):
            tx_index, timestamp, value = transaction.split('+')
            if (int(time_from) <= int(timestamp) and int(time_to) >= int(timestamp)
                    and int(val_from) <= int(value) and int(val_to) >= int(value)):
                counter += 1
                if counter > int(no_tx_list):
                    break
                raw_tx = self.transaction_db.get(tx_index.encode())
                output_transactions.append(coder.decode_transaction(raw_tx))

        del address['inputTransactionIndexes']
        del address['outputTransactionIndexes']
        address['inputTransactions'] = input_transactions
        address['outputTransactions'] = output_transactions
        return address

    def get_balance(self, addr: str) -> Union[str, None]:
        """
        Get balance of an address.

        Args:
            addr: Requested address.

        Returns:
            Current balance of an address.
        """
        raw_address = self.address_db.get(addr.encode())
        if raw_address is None:
            return None
        address = coder.decode_address(raw_address)

        return address['balance']
