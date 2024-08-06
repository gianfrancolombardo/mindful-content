import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

class FirebaseDB:
    def __init__(self, cred_path):
        """Initialize the connection with Firestore"""
        self.cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()
        print('Connected to Firestore!')

    def create_document(self, collection_name, document_data, document_id=None):
        """Create a new document in the specified collection"""
        try:
            if document_id:
                self.db.collection(collection_name).document(document_id).set(document_data)
            else:
                self.db.collection(collection_name).add(document_data)
        except Exception as e:
            raise Exception(f'Error creating document: {str(e)}')

    def read_document(self, collection_name, document_id):
        """Read a document from the specified collection"""
        try:
            doc = self.db.collection(collection_name).document(document_id).get()
            if doc.exists:
                return doc.to_dict()
            else:
                raise Exception('Document not found')
        except Exception as e:
            raise Exception(f'Error reading document: {str(e)}')

    def read_document_by_property(self, collection_name, property_name, property_value):
        """Read documents from the specified collection based on a property"""
        try:
            field_filter = FieldFilter(property_name, "==", property_value)
            docs = self.db.collection(collection_name).where(filter=field_filter).stream()
            
            results = [doc.to_dict() for doc in docs]
            return results if results else None
        except Exception as e:
            raise Exception(f'Error reading documents by property: {str(e)}')

    def read_all_documents(self, collection_name, order_by=None):
        """Read all documents from the specified collection"""
        try:
            collection_ref = self.db.collection(collection_name)
            if order_by:
                docs = collection_ref.order_by(order_by).stream()
            else:
                docs = collection_ref.stream()
            results = []
            for doc in docs:
                results.append(doc.to_dict())
            if results:
                return results
            else:
                return []
        except Exception as e:
            raise Exception(f'Error reading documents: {str(e)}')

    def update_document(self, collection_name, document_id, update_data):
        """Update an existing document in the specified collection"""
        try:
            self.db.collection(collection_name).document(document_id).update(update_data)
        except Exception as e:
            raise Exception(f'Error updating document: {str(e)}')

    def delete_document(self, collection_name, document_id):
        """Delete a document from the specified collection"""
        try:
            self.db.collection(collection_name).document(document_id).delete()
        except Exception as e:
            raise Exception(f'Error deleting document: {str(e)}')