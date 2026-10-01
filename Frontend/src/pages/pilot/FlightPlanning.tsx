import React, { useState, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { CalendarDaysIcon, ClockIcon, PlaneTakeoffIcon, SendIcon, XIcon, CheckCircleIcon, Loader2Icon, InfoIcon } from 'lucide-react';
import { PageHeading } from '../../components/pilot/PageHeading';
import { flightLevels, requestMaps, requestPreview } from '../../data/flight';
import { useAuth } from '../../contexts/AuthContext';

const fieldClass =
  'h-11 w-full rounded-lg border border-lineStrong bg-ink px-3 text-sm text-faint placeholder:text-muted transition-colors duration-150 ease-out focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent';

const getInitialUTCDate = () => {
  const now = new Date();
  const yyyy = now.getUTCFullYear();
  const mm = String(now.getUTCMonth() + 1).padStart(2, '0');
  const dd = String(now.getUTCDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
};

const getInitialUTCTime = () => {
  const now = new Date();
  const hh = String(now.getUTCHours()).padStart(2, '0');
  const min = String(now.getUTCMinutes()).padStart(2, '0');
  return `${hh}:${min}`;
};

export function FlightPlanning() {
  const navigate = useNavigate();
  const [levels, setLevels] = useState<string[]>(['FL390', 'FL340']);
  const [maps, setMaps] = useState<string[]>(requestMaps);
  
  // Form State
  const [departure, setDeparture] = useState("VCBI");
  const [destination, setDestination] = useState("WSSS");
  const [departureDate, setDepartureDate] = useState(getInitialUTCDate());
  const [departureTime, setDepartureTime] = useState(getInitialUTCTime());
  const [flightNo, setFlightNo] = useState("UL604");
  const [area, setArea] = useState("Area D");
  
  // Modal & API State
  const [showModal, setShowModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [flightDuration, setFlightDuration] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const { user } = useAuth();

  React.useEffect(() => {
    // Fetch next flight based on local time
    axios.get('http://localhost:8000/pilot/next-flight')
      .then(res => {
        if (res.data && res.data.flight_no) {
          setFlightNo(res.data.flight_no);
          setDestination(res.data.destination);
          
          if (res.data.departure_time_local) {
            setDepartureTime(res.data.departure_time_local);
          }
          
          if (res.data.duration_mins) {
            const h = Math.floor(res.data.duration_mins / 60);
            const m = res.data.duration_mins % 60;
            setFlightDuration(`${h}h ${m}m`);
          }
        }
      })
      .catch(err => console.error("Could not fetch next flight:", err));
  }, []);

  // Fetch real-time flight data when destination changes manually
  React.useEffect(() => {
    if (destination && destination.length >= 3) {
      
      // Auto-assign Area based on common destination ICAO codes
      const dest = destination.toUpperCase();
      const eastDestinations = ['WSSS', 'WMKK', 'VTBS', 'VHHH', 'YSSY', 'YMML'];
      const westDestinations = ['OMDB', 'OTHH', 'EGLL', 'VABB', 'VIDP', 'OKBK', 'OAKB'];
      const southDestinations = ['VRMM', 'FIMP', 'FAOR'];
      
      if (eastDestinations.includes(dest)) {
        setArea('Area E');
      } else if (southDestinations.includes(dest)) {
        setArea('Area F');
      } else {
        setArea('Area D'); // Default for west/others
      }

      axios.get(`http://localhost:8000/pilot/flight-info?destination=${destination}`)
        .then(res => {
          if (res.data && res.data.flight_no) {
            setFlightNo(res.data.flight_no);
            if (res.data.duration_mins) {
              const h = Math.floor(res.data.duration_mins / 60);
              const m = res.data.duration_mins % 60;
              setFlightDuration(`${h}h ${m}m`);
            }
          }
        })
        .catch(err => console.error("Could not fetch flight info:", err));
    }
  }, [destination]);

  // Fetch real-time flight data when time changes
  React.useEffect(() => {
    if (departureTime && departureTime.length === 5) { // e.g. "03:25"
      axios.get(`http://localhost:8000/pilot/flight-info-by-time?time_local=${departureTime}`)
        .then(res => {
          if (res.data && res.data.flight_no) {
            setFlightNo(res.data.flight_no);
            setDestination(res.data.destination);
            if (res.data.duration_mins) {
              const h = Math.floor(res.data.duration_mins / 60);
              const m = res.data.duration_mins % 60;
              setFlightDuration(`${h}h ${m}m`);
            }
          }
        })
        .catch(err => console.error("Could not fetch flight info by time:", err));
    }
  }, [departureTime]);

  // Reference for datetime input
  const dateInputRef = useRef<HTMLInputElement>(null);

  // Parse raw date and time strings to Aviation UTC
  const getAviationTime = (dStr: string, tStr: string) => {
    if (!dStr || !tStr) return '';
    try {
      const day = dStr.split('-')[2];
      const hour = tStr.split(':')[0];
      const minute = tStr.split(':')[1];
      if (!day || !hour || !minute) return '';
      return `${day}${hour}${minute}Z`;
    } catch {
      return '';
    }
  };

  const toggle = (value: string, list: string[], set: (next: string[]) => void) => {
    set(list.includes(value) ? list.filter((item) => item !== value) : [...list, value]);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (isLoading) return;
    setIsLoading(true);
    setError(null);
    abortControllerRef.current = new AbortController();

    try {
      const response = await axios.post('http://localhost:8000/pilot/flight-plan', {
        departure,
        destination,
        departure_time: `${departureDate}T${departureTime}`,
        area,
        flight_levels: levels,
        maps,
        pilot_reference: user?.reference || "guest",
        flight_no: flightNo,
        preview_only: true
      }, {
        signal: abortControllerRef.current.signal
      });
      
      if (response.data && response.data.document_url) {
        setPreviewUrl(response.data.document_url);
        setShowModal(true);
      }
    } catch (err: any) {
      if (axios.isCancel(err)) {
        console.log("Request canceled by user");
        setError("Generation canceled.");
      } else {
        console.error(err);
        setError(err.response?.data?.detail || "Failed to generate preview document.");
      }
      setTimeout(() => setError(null), 8000);
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const confirmAndGenerate = async () => {
    if (isLoading) return;
    setIsLoading(true);
    setError(null);
    abortControllerRef.current = new AbortController();

    try {
      const response = await axios.post('http://localhost:8000/pilot/flight-plan', {
        departure,
        destination,
        departure_time: `${departureDate}T${departureTime}`,
        area,
        flight_levels: levels,
        maps,
        pilot_reference: user?.reference || "guest",
        flight_no: flightNo,
        preview_only: false,
        preview_url: previewUrl
      }, {
        signal: abortControllerRef.current.signal
      });
      
      if (response.data && response.data.document_url) {
        // Fetch the PDF as a blob to force a download prompt across origins
        const pdfResponse = await axios.get(response.data.document_url, { 
          responseType: 'blob',
          signal: abortControllerRef.current.signal
        });
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
        setPreviewUrl(null);
      }
    } catch (err: any) {
      if (axios.isCancel(err)) {
        console.log("Download canceled by user");
        setError("Download canceled.");
      } else {
        console.error(err);
        setError(err.response?.data?.detail || "Failed to generate flight plan.");
      }
      setTimeout(() => setError(null), 8000);
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsLoading(false);
  };

  return (
    <div className="w-full space-y-6 relative">
      <PageHeading
        eyebrow="Pilot operations"
        title="Flight Planning Request"
        description="Create an ICAO-aligned aviation weather briefing request for meteorological review."
      />

      {error && !showModal && (
        <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-4 mb-6 flex items-start gap-3 transition-all duration-300">
          <div className="rounded-full bg-red-500/20 p-1 mt-0.5">
            <XIcon className="h-4 w-4 text-red-400" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-red-400">Request Failed</h3>
            <p className="mt-1 text-xs text-red-400/80">{error}</p>
          </div>
        </div>
      )}

      <form className="w-full space-y-6" onSubmit={handleSubmit}>
        <section className="rounded-xl border border-line bg-panel p-6">
          <div className="flex flex-col gap-4 border-b border-line pb-5 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="text-lg font-bold text-white">Flight planning request</h2>
              <p className="mt-1 text-xs text-subtle">MET briefing criteria · ICAO compliant</p>
            </div>
            <span className="inline-flex items-center gap-2 rounded-lg border border-accent/60 bg-accent/15 px-3 py-2 text-xs font-semibold text-sky-pale">
              <PlaneTakeoffIcon className="h-[15px] w-[15px]" aria-hidden="true" />
              VCBI departure
            </span>
          </div>

          <div className="grid gap-5 pt-6 lg:grid-cols-3">
            <label className="block sm:max-w-xs">
              <span className="text-xs font-medium text-subtle">Departure airport code</span>
              <input 
                className={`${fieldClass} mt-1.5`} 
                value={departure}
                onChange={(e) => setDeparture(e.target.value.toUpperCase())}
                placeholder="VCBI" 
                required
              />
            </label>

            <label className="block sm:max-w-xs">
              <span className="text-xs font-medium text-subtle">Flight Number</span>
              <input 
                className={`${fieldClass} mt-1.5`} 
                value={flightNo}
                onChange={(e) => setFlightNo(e.target.value.toUpperCase())}
                placeholder="e.g., UL604" 
                required
              />
            </label>

            <label className="block">
              <span className="text-xs font-medium text-subtle">Departure date &amp; time (Select in UTC)</span>
              <div className="mt-1.5 flex gap-2">
                <div className="relative flex-1">
                  <CalendarDaysIcon
                    className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
                    aria-hidden="true"
                  />
                  <input
                    type="date"
                    value={departureDate}
                    onChange={(e) => setDepartureDate(e.target.value)}
                    className={`${fieldClass} pl-9 cursor-pointer`}
                    required
                  />
                </div>
                <div className="relative w-[120px]">
                  <ClockIcon
                    className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
                    aria-hidden="true"
                  />
                  <input
                    type="time"
                    lang="en-GB"
                    value={departureTime}
                    onChange={(e) => setDepartureTime(e.target.value)}
                    className={`${fieldClass} pl-9 cursor-pointer`}
                    required
                  />
                </div>
              </div>
              <p className="mt-1 text-[11px] text-sky-pale/60">
                Aviation format: <span className="font-mono text-sky-pale">{getAviationTime(departureDate, departureTime)}</span>
              </p>
            </label>

            <label className="block sm:max-w-xs">
              <span className="flex items-center justify-between text-xs font-medium text-subtle">
                <span>Destination airport code</span>
                {flightDuration && (
                  <span className="flex items-center gap-1 text-sky-pale">
                    <InfoIcon className="h-3 w-3" />
                    Est. Duration: {flightDuration}
                  </span>
                )}
              </span>
              <input 
                className={`${fieldClass} mt-1.5`} 
                value={destination}
                onChange={(e) => setDestination(e.target.value.toUpperCase())}
                placeholder="WSSS" 
                required
              />
            </label>

            <label className="block sm:max-w-xs">
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
        </section>

        <section className="rounded-xl border border-line bg-panel p-6">
          <fieldset>
            <legend className="text-lg font-bold text-white">Flight levels</legend>
            <p className="mt-1 text-xs text-subtle mb-4">Select the cruising altitudes for the flight.</p>
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
        </section>

        <section className="rounded-xl border border-line bg-panel p-6">
          <fieldset>
            <legend className="text-lg font-bold text-white">Request maps</legend>
            <p className="mt-1 text-xs text-subtle mb-4">Select the required meteorological maps.</p>
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
        </section>

        <section className="rounded-xl border border-line bg-panel p-6">
          <div className="rounded-lg border border-line bg-ink p-4">
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
                <dd className="mt-0.5 text-sm text-faint">VCBI Met Forecast Desk</dd>
              </div>
            </dl>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="mt-6 inline-flex h-10 items-center gap-2 rounded-lg bg-accent px-4 text-sm font-bold text-white transition-colors duration-150 ease-out hover:bg-sky-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-bright disabled:opacity-70 disabled:cursor-not-allowed"
          >
            <SendIcon className="h-4 w-4" aria-hidden="true" />
            Review flight request
          </button>
        </section>
      </form>

      {/* Confirmation Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
          <div className="w-full max-w-4xl rounded-xl border border-line bg-panel shadow-2xl overflow-hidden">
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
              {previewUrl ? (
                <iframe src={previewUrl} className="w-full h-[65vh] rounded-md border border-line" title="PDF Preview" />
              ) : (
                <div className="flex items-center justify-center h-[65vh] text-muted">
                  Loading preview...
                </div>
              )}
              {error && (
                <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-red-400 text-sm">
                  {error}
                </div>
              )}
            </div>
            
            <div className="flex items-center justify-end gap-3 border-t border-line bg-ink/50 px-6 py-4">
              <button
                onClick={() => {
                  setShowModal(false);
                  setPreviewUrl(null);
                }}
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

      {/* Full-screen Loading Overlay */}
      {isLoading && createPortal(
        <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-black/60 backdrop-blur-md">
          <PlaneTakeoffIcon className="h-16 w-16 animate-bounce text-sky-400" />
          <h2 className="mt-6 text-xl font-bold text-white">Generating Flight Briefing</h2>
          <p className="mt-2 text-sm text-sky-pale animate-pulse">Fetching meteorological data and rendering PDF...</p>
          <button 
            onClick={handleCancel}
            className="mt-8 rounded-lg border border-red-500/50 bg-red-500/20 px-6 py-2.5 text-sm font-bold text-red-400 transition-colors hover:bg-red-500/30"
          >
            Cancel Generation
          </button>
        </div>,
        document.body
      )}
    </div>
  );
}