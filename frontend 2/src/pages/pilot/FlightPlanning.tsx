import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { CalendarDaysIcon, ClockIcon, PlaneTakeoffIcon, SendIcon, XIcon, CheckCircleIcon, Loader2Icon } from 'lucide-react';
import { PageHeading } from '../../components/pilot/PageHeading';
import { flightLevels, requestMaps, requestPreview } from '../../data/flight';

const fieldClass =
  'h-11 w-full rounded-lg border border-lineStrong bg-ink px-3 text-sm text-faint placeholder:text-muted transition-colors duration-150 ease-out focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent';

export function FlightPlanning() {
  const navigate = useNavigate();
  const [levels, setLevels] = useState<string[]>(['FL390', 'FL340', 'FL180', 'FL100']);
  const [maps, setMaps] = useState<string[]>(requestMaps);
  
  // Form State
  const [departure, setDeparture] = useState("VCBI");
  const [destination, setDestination] = useState("WSSS");
  const [departureTime, setDepartureTime] = useState("2026-06-18T08:30");
  const [area, setArea] = useState("Area D");
  
  // Modal & API State
  const [showModal, setShowModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reference for datetime input
  const dateInputRef = useRef<HTMLInputElement>(null);

  // Parse raw datetime-local string to Aviation UTC
  const getAviationTime = (dtStr: string) => {
    if (!dtStr || !dtStr.includes('T')) return '';
    const [datePart, timePart] = dtStr.split('T');
    const day = datePart.split('-')[2];
    const hour = timePart.split(':')[0];
    const minute = timePart.split(':')[1];
    return `${day}${hour}${minute}Z`;
  };

  const toggle = (value: string, list: string[], set: (next: string[]) => void) => {
    set(list.includes(value) ? list.filter((item) => item !== value) : [...list, value]);
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setShowModal(true);
  };

  const confirmAndGenerate = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.post('http://localhost:8000/pilot/flight-plan', {
        departure,
        destination,
        departure_time: departureTime,
        area,
        flight_levels: levels,
        maps
      });
      
      if (response.data && response.data.document_url) {
        // Fetch the PDF as a blob to force a download prompt across origins
        const pdfResponse = await axios.get(response.data.document_url, { responseType: 'blob' });
        const blobUrl = window.URL.createObjectURL(new Blob([pdfResponse.data]));
        
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = `Flight_Briefing_${departure}_to_${destination}.pdf`;
        document.body.appendChild(link);
        link.click();
        
        // Cleanup
        document.body.removeChild(link);
        window.URL.revokeObjectURL(blobUrl);
        
        setShowModal(false);
      }
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to generate document.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full space-y-6 relative">
      <PageHeading
        eyebrow="Pilot operations"
        title="Flight Planning Request"
        description="Create an ICAO-aligned aviation weather briefing request for meteorological review."
      />

      <form className="w-full space-y-6" onSubmit={handleSubmit}>
        <section className="rounded-xl border border-line bg-panel p-6">
          <div className="flex flex-col gap-4 border-b border-line pb-5 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="text-lg font-bold text-white">Flight planning request</h2>
              <p className="mt-1 text-xs text-subtle">MET briefing criteria · ICAO compliant</p>
            </div>
            <span className="inline-flex items-center gap-2 rounded-lg border border-accent/60 bg-accent/15 px-3 py-2 text-xs font-semibold text-sky-pale">
              <PlaneTakeoffIcon className="h-[15px] w-[15px]" aria-hidden="true" />
              CMB / VCBI departure
            </span>
          </div>

          <div className="grid gap-5 pt-6 lg:grid-cols-2">
            <label className="block">
              <span className="text-xs font-medium text-subtle">Departure airport code</span>
              <input 
                className={`${fieldClass} mt-1.5`} 
                value={departure}
                onChange={(e) => setDeparture(e.target.value.toUpperCase())}
                placeholder="VCBI" 
                required
              />
            </label>

            <label className="block">
              <span className="text-xs font-medium text-subtle">Departure date &amp; time (Select in UTC)</span>
              <div 
                className="relative mt-1.5 cursor-pointer"
                onClick={() => dateInputRef.current?.showPicker && dateInputRef.current.showPicker()}
              >
                <ClockIcon
                  className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
                  aria-hidden="true"
                />
                <input
                  type="datetime-local"
                  ref={dateInputRef}
                  value={departureTime}
                  onChange={(e) => setDepartureTime(e.target.value)}
                  className={`${fieldClass} pl-9 pr-10 cursor-pointer`}
                  required
                />
                <CalendarDaysIcon
                  className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted hover:text-accent transition-colors"
                  aria-hidden="true"
                />
              </div>
              <p className="mt-1 text-[11px] text-sky-pale/60">
                Aviation format: <span className="font-mono text-sky-pale">{getAviationTime(departureTime)}</span>
              </p>
            </label>

            <label className="block">
              <span className="text-xs font-medium text-subtle">Destination airport code</span>
              <input 
                className={`${fieldClass} mt-1.5`} 
                value={destination}
                onChange={(e) => setDestination(e.target.value.toUpperCase())}
                placeholder="WSSS" 
                required
              />
            </label>

            <label className="block">
              <span className="text-xs font-medium text-subtle">Area</span>
              <select 
                className={`${fieldClass} mt-1.5`} 
                value={area}
                onChange={(e) => setArea(e.target.value)}
              >
                <option>Area D</option>
                <option>Area E</option>
                <option>Area F</option>
              </select>
            </label>
          </div>

          <fieldset className="pt-6">
            <legend className="text-xs font-medium text-subtle">Flight levels</legend>
            <div className="mt-2 grid grid-cols-2 gap-3 rounded-lg border border-lineStrong bg-ink p-4 sm:grid-cols-3 lg:grid-cols-5">
              {flightLevels.map((level) => (
                <label key={level} className="flex items-center gap-2 text-sm text-faint cursor-pointer">
                  <input
                    type="checkbox"
                    checked={levels.includes(level)}
                    onChange={() => toggle(level, levels, setLevels)}
                    className="h-4 w-4 rounded border-lineStrong bg-panel text-accent focus:ring-accent"
                  />
                  {level}
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="pt-6">
            <legend className="text-xs font-semibold tracking-wide text-subtle">Request maps</legend>
            <div className="mt-2 space-y-3 rounded-lg border border-line bg-ink p-4">
              {requestMaps.map((map) => (
                <label key={map} className="flex items-center gap-3 text-sm text-faint cursor-pointer">
                  <input
                    type="checkbox"
                    checked={maps.includes(map)}
                    onChange={() => toggle(map, maps, setMaps)}
                    className="h-4 w-4 rounded border-lineStrong bg-panel text-accent focus:ring-accent"
                  />
                  {map}
                </label>
              ))}
            </div>
          </fieldset>

          <div className="mt-6 rounded-lg border border-line bg-ink p-4">
            <p className="text-xs font-semibold tracking-wide text-muted">Request preview</p>
            <dl className="mt-3 grid gap-4 sm:grid-cols-3">
              <div>
                <dt className="text-xs text-muted">Route</dt>
                <dd className="mt-0.5 text-sm text-faint font-semibold">{departure} → {destination}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted">Flight Levels Selected</dt>
                <dd className="mt-0.5 text-sm text-faint">{levels.length} levels</dd>
              </div>
              <div>
                <dt className="text-xs text-muted">Approval routing</dt>
                <dd className="mt-0.5 text-sm text-faint">BIA Met Forecast Desk</dd>
              </div>
            </dl>
          </div>

          <button
            type="submit"
            className="mt-6 inline-flex h-10 items-center gap-2 rounded-lg bg-accent px-4 text-sm font-bold text-white transition-colors duration-150 ease-out hover:bg-sky-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-bright"
          >
            <SendIcon className="h-4 w-4" aria-hidden="true" />
            Review flight request
          </button>
        </section>
      </form>

      {/* Confirmation Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
          <div className="w-full max-w-lg rounded-xl border border-line bg-panel shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between border-b border-line bg-ink/50 px-6 py-4">
              <h3 className="text-lg font-bold text-white">Confirm Request Details</h3>
              <button 
                onClick={() => setShowModal(false)}
                className="text-muted hover:text-white transition-colors"
              >
                <XIcon className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-ink p-3 border border-line">
                  <p className="text-xs text-muted mb-1">Departure</p>
                  <p className="font-bold text-white">{departure}</p>
                  <p className="text-xs text-faint mt-1">{departureTime.replace('T', ' ')} UTC</p>
                </div>
                <div className="rounded-lg bg-ink p-3 border border-line">
                  <p className="text-xs text-muted mb-1">Destination</p>
                  <p className="font-bold text-white">{destination}</p>
                  <p className="text-xs text-faint mt-1">Area: {area}</p>
                </div>
              </div>
              
              <div>
                <h4 className="text-xs font-semibold text-subtle uppercase mb-2">Requested Levels</h4>
                <div className="flex flex-wrap gap-2">
                  {levels.map(lvl => (
                    <span key={lvl} className="bg-lineStrong text-faint px-2 py-1 rounded text-xs">
                      {lvl}
                    </span>
                  ))}
                  {levels.length === 0 && <span className="text-xs text-muted">None selected</span>}
                </div>
              </div>
              
              <div>
                <h4 className="text-xs font-semibold text-subtle uppercase mb-2">Requested Maps</h4>
                <div className="flex flex-wrap gap-2">
                  {maps.map(m => (
                    <span key={m} className="bg-lineStrong text-faint px-2 py-1 rounded text-xs">
                      {m}
                    </span>
                  ))}
                  {maps.length === 0 && <span className="text-xs text-muted">None selected</span>}
                </div>
              </div>

              {error && (
                <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-red-400 text-sm">
                  {error}
                </div>
              )}
            </div>
            
            <div className="flex items-center justify-end gap-3 border-t border-line bg-ink/50 px-6 py-4">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 rounded-lg text-sm font-medium text-faint hover:text-white transition-colors"
                disabled={isLoading}
              >
                Cancel
              </button>
              <button
                onClick={confirmAndGenerate}
                disabled={isLoading}
                className="inline-flex h-10 items-center gap-2 rounded-lg bg-accent px-4 text-sm font-bold text-white transition-colors duration-150 ease-out hover:bg-sky-400 disabled:opacity-70"
              >
                {isLoading ? (
                  <>
                    <Loader2Icon className="h-4 w-4 animate-spin" />
                    Generating PDF...
                  </>
                ) : (
                  <>
                    <CheckCircleIcon className="h-4 w-4" />
                    Confirm & Generate
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}