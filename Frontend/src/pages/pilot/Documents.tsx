import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PageHeading } from '../../components/pilot/PageHeading';
import { DocumentsTable } from '../../components/pilot/DocumentsTable';
import type { BriefingDocument } from '../../types/aviation';
import { useAuth } from '../../contexts/AuthContext';

export function Documents() {
  const [documents, setDocuments] = useState<BriefingDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    if (user?.reference) {
      axios.get(`http://localhost:8000/pilot/my-documents?pilot_reference=${user.reference}`)
        .then(res => {
          setDocuments(res.data);
        })
        .catch(err => console.error("Error fetching documents:", err))
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [user]);

  return (
    <div className="w-full space-y-6">
      <PageHeading
        eyebrow="Flight operations"
        title="My documents"
        description="Recent aviation weather briefings and flight history" />
      
      <section className="rounded-xl border border-line bg-panel p-5">
        {isLoading ? (
          <div className="text-center py-10 text-muted">Loading documents...</div>
        ) : documents.length > 0 ? (
          <DocumentsTable documents={documents} />
        ) : (
          <div className="text-center py-10 text-muted">No documents found.</div>
        )}
      </section>
    </div>
  );
}