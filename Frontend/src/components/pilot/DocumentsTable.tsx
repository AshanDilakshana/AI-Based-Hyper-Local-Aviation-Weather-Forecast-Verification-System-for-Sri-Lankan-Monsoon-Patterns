import React from 'react';
import { DownloadIcon } from 'lucide-react';
import type { BriefingDocument } from '../../types/aviation';
import { StatusPill } from './StatusPill';

interface DocumentsTableProps {
  documents: BriefingDocument[];
  showStatus?: boolean;
}

export function DocumentsTable({ documents, showStatus = true }: DocumentsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] border-collapse text-left">
        <thead>
          <tr className="border-b border-line">
            <th className="pb-2 text-xs font-medium tracking-wide text-muted">Reference</th>
            <th className="pb-2 text-xs font-medium tracking-wide text-muted">Flight</th>
            <th className="pb-2 text-xs font-medium tracking-wide text-muted">Forecast date</th>
            {showStatus &&
            <th className="pb-2 text-xs font-medium tracking-wide text-muted">Status</th>
            }
            <th className="pb-2 text-right text-xs font-medium tracking-wide text-muted">
              <span className="sr-only">Download</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) =>
          <tr key={doc.reference} className="border-b border-slate-800 last:border-b-0">
              <td className="py-5 text-sm font-medium text-white">{doc.reference}</td>
              <td className="py-5 text-sm text-faint">{doc.route}</td>
              <td className="py-5 text-sm text-subtle">{doc.forecastDate}</td>
              {showStatus &&
            <td className="py-5">
                  <StatusPill status={doc.status} />
                </td>
            }
              <td className="py-5 text-right">
                <button
                type="button"
                className="rounded-md p-1.5 text-subtle transition-colors duration-150 ease-out hover:bg-white/5 hover:text-sky-bright"
                aria-label={`Download ${doc.reference}`}>
                
                  <DownloadIcon className="h-[17px] w-[17px]" aria-hidden="true" />
                </button>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>);

}