import React from 'react';
import { PageHeading } from '../../components/pilot/PageHeading';
import { DocumentsTable } from '../../components/pilot/DocumentsTable';
import { documents } from '../../data/documents';

export function Documents() {
  return (
    <div className="w-full space-y-6">
      <PageHeading
        eyebrow="Flight operations"
        title="My documents"
        description="Recent aviation weather briefings and flight history" />
      

      <section className="rounded-xl border border-line bg-panel p-5">
        <DocumentsTable documents={documents} />
      </section>
    </div>);

}