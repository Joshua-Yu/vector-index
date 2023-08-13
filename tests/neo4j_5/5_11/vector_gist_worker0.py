from neo4j import GraphDatabase
import numpy as np
import struct
import time
from datetime import datetime

JOB_ID = 0
TOTAL_JOBS = 1
dimension = 960
batch = 5000 * TOTAL_JOBS

class VectorExample:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()
        self.file.close()

    def create_vectors(self):
        with self.driver.session() as session:
            
            self.file = open("gist_base.fvecs", "rb")
            #binary = self.file.read(4)
            #dimension = struct.unpack("i", binary)[0]
            #print("dimension : " + str(dimension))
            batchCount = 0
            start = time.perf_counter();
            # while  session.execute_write(self._create_vector_node, self.file, batch, dimension) == batch:
            while  session.execute_write(self._create_vector_node, self.file, batch, dimension) > 0:
                batchCount = batchCount + 1

                current = time.perf_counter()
                progress = batchCount * batch
                print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " - Completed ", progress, " at ", int(progress/(current - start)), " nodes/s")

                #if batchCount == 4:
                #    break

    @staticmethod
    def _create_vector_node_parallel(tx, file, batch, dimension):
        actual = 0
        vectors = []
        for i in range(batch):
            numbers = []
            # skip the first 4 bytes
            binary = file.read(4)             
            for j in range(dimension):
                binary = 0
                # Unpack the binary data into a floating point number using IEEE 754 single precision
                binary = file.read(4)
                if not binary:
                    break
                numbers.append(struct.unpack("f", binary)[0])
            if not binary:
                break
            vectors.append(numbers)
            actual = i + 1
        
        cypher1 = "\"WITH $vectors as vecs UNWIND vecs as vec RETURN vec;\""
        cypher2 = "\"WITH vec CREATE (n:Embedding) WITH n , vec CALL db.create.setVectorProperty(n,'data',vec) YIELD node RETURN true;\""
        tx.run(
            "CALL apoc.periodic.iterate(" + cypher1 + "," + cypher2 + "," + 
            "{batchSize:500, concurrency:5, iterateList:true, parallel:true, params:{vectors:$vectors}})"
            "YIELD batches, total, errorMessages RETURN batches, total, errorMessages;", vectors=vectors)
        return actual
    
    @staticmethod
    def _create_vector_node(tx, file, batch, dimension):
        actual = 0
        vectors = []
        for i in range(batch):
            numbers = []
            # skip the first 4 bytes
            binary = file.read(4) 
            for j in range(dimension):
                binary = 0
                # Unpack the binary data into a floating point number using IEEE 754 single precision
                binary = file.read(4)
                if not binary:
                    break
                numbers.append(struct.unpack("f", binary)[0])
            if not binary:
                break

            if i % TOTAL_JOBS != JOB_ID:
                continue
            
            vectors.append(numbers)
            actual = i + 1
        

        tx.run(
            "WITH $vectors as vecs "
            "UNWIND vecs as vec "
            "CREATE (n:Embedding) "
            "WITH n , vec "
            "CALL db.create.setVectorProperty(n,'value',vec) YIELD node "
            "RETURN count(node) ", vectors=vectors)
        return actual

if __name__ == "__main__":
    reader = VectorExample("bolt://localhost:7687", "neo4j", "Neo4j123")
    reader.create_vectors()
    print("done")
    reader.close()


