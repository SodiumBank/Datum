"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

/**
 * Ops UI: Execution Outputs Viewer (Sprint 2: Read-Only)
 * 
 * SPRINT 2 GUARDRAIL: This component is read-only.
 * NO export buttons, NO edit options, NO production-ready artifacts.
 * Outputs are intent-only in Sprint 2.
 */

interface ExecutionOutputs {
  plan_id: string;
  quote_id: string;
  outputs: {
    stencil?: {
      foil_thickness_mm: number;
      apertures: Array<{
        refdes: string;
        package: string;
        aperture_type: string;
      }>;
    };
    placement?: {
      placements: Array<{
        refdes: string;
        package: string;
        x_mm: number;
        y_mm: number;
        rotation_deg: number;
        side: string;
      }>;
    };
    selective_solder?: {
      locations: Array<{
        refdes: string;
        package: string;
        solder_type: string;
      }>;
    };
    lead_form?: {
      entries: Array<{
        refdes: string;
        package: string;
        bend_angle_deg: number;
      }>;
    };
    programming?: {
      components: Array<{
        refdes: string;
        package: string;
        programming_type: string;
      }>;
    };
  };
}

export default function OutputsViewer() {
  const searchParams = useSearchParams();
  const planId = searchParams.get("plan_id");
  const [outputs, setOutputs] = useState<ExecutionOutputs | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchOutputs() {
      if (!planId) {
        setError("Missing plan_id");
        setLoading(false);
        return;
      }

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${apiUrl}/outputs/${planId}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch outputs: ${response.statusText}`);
        }

        const data = await response.json();
        setOutputs(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch outputs");
      } finally {
        setLoading(false);
      }
    }

    fetchOutputs();
  }, [planId]);

  if (loading) {
    return <div className="p-8">Loading execution outputs...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-600">Error: {error}</div>;
  }

  if (!outputs) {
    return <div className="p-8">Execution outputs not found</div>;
  }

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">Execution Outputs Viewer</h1>
        <p className="text-gray-600">
          Plan: {outputs.plan_id} | Quote: {outputs.quote_id}
        </p>
        <p className="text-sm text-gray-500 mt-2">
          Sprint 2: Read-only intent. Not production-ready.
        </p>
      </div>

      {/* Stencil Intent */}
      {outputs.outputs.stencil && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Stencil Intent</h2>
          <div className="border rounded p-4 bg-white">
            <div className="mb-2">
              <span className="font-medium">Foil Thickness: </span>
              <span>{outputs.outputs.stencil.foil_thickness_mm} mm</span>
            </div>
            <div className="mt-4">
              <span className="font-medium">Apertures: </span>
              <span>{outputs.outputs.stencil.apertures.length} components</span>
            </div>
            <div className="mt-4 max-h-64 overflow-y-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left">RefDes</th>
                    <th className="px-4 py-2 text-left">Package</th>
                    <th className="px-4 py-2 text-left">Type</th>
                  </tr>
                </thead>
                <tbody>
                  {outputs.outputs.stencil.apertures.slice(0, 20).map((apt, idx) => (
                    <tr key={idx} className="border-t">
                      <td className="px-4 py-2">{apt.refdes}</td>
                      <td className="px-4 py-2">{apt.package}</td>
                      <td className="px-4 py-2">{apt.aperture_type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* Placement Intent */}
      {outputs.outputs.placement && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Placement Intent</h2>
          <div className="border rounded p-4 bg-white">
            <div className="mb-4">
              <span className="font-medium">Placements: </span>
              <span>{outputs.outputs.placement.placements.length} components</span>
            </div>
            <div className="max-h-64 overflow-y-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left">RefDes</th>
                    <th className="px-4 py-2 text-left">X (mm)</th>
                    <th className="px-4 py-2 text-left">Y (mm)</th>
                    <th className="px-4 py-2 text-left">Rotation</th>
                    <th className="px-4 py-2 text-left">Side</th>
                  </tr>
                </thead>
                <tbody>
                  {outputs.outputs.placement.placements.slice(0, 20).map((plc, idx) => (
                    <tr key={idx} className="border-t">
                      <td className="px-4 py-2">{plc.refdes}</td>
                      <td className="px-4 py-2">{plc.x_mm.toFixed(2)}</td>
                      <td className="px-4 py-2">{plc.y_mm.toFixed(2)}</td>
                      <td className="px-4 py-2">{plc.rotation_deg}°</td>
                      <td className="px-4 py-2">{plc.side}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* Selective Solder Intent */}
      {outputs.outputs.selective_solder && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Selective Solder Intent</h2>
          <div className="border rounded p-4 bg-white">
            <div className="mb-4">
              <span className="font-medium">Locations: </span>
              <span>{outputs.outputs.selective_solder.locations.length} PTH components</span>
            </div>
            <div className="space-y-2">
              {outputs.outputs.selective_solder.locations.slice(0, 10).map((loc, idx) => (
                <div key={idx} className="text-sm">
                  <span className="font-medium">{loc.refdes}</span>
                  <span className="text-gray-600 ml-2">({loc.package})</span>
                  <span className="text-gray-500 ml-2">- {loc.solder_type}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Lead Form Intent */}
      {outputs.outputs.lead_form && outputs.outputs.lead_form.entries.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Lead Form Intent</h2>
          <div className="border rounded p-4 bg-white">
            <div className="space-y-2">
              {outputs.outputs.lead_form.entries.slice(0, 10).map((entry, idx) => (
                <div key={idx} className="text-sm">
                  <span className="font-medium">{entry.refdes}</span>
                  <span className="text-gray-600 ml-2">({entry.package})</span>
                  <span className="text-gray-500 ml-2">- {entry.bend_angle_deg}°</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Programming Intent */}
      {outputs.outputs.programming && outputs.outputs.programming.components.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Programming Intent</h2>
          <div className="border rounded p-4 bg-white">
            <div className="space-y-2">
              {outputs.outputs.programming.components.slice(0, 10).map((comp, idx) => (
                <div key={idx} className="text-sm">
                  <span className="font-medium">{comp.refdes}</span>
                  <span className="text-gray-600 ml-2">({comp.package})</span>
                  <span className="text-gray-500 ml-2">- {comp.programming_type}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Sprint 2 Notice */}
      <div className="mt-8 p-4 bg-gray-100 rounded border-l-4 border-gray-400">
        <p className="text-sm font-medium text-gray-800">
          Sprint 2: Read-Only Intent Layer
        </p>
        <p className="text-xs text-gray-600 mt-1">
          These outputs are intent-only. No machine files, no production-ready artifacts.
          Export functionality will be available in Sprint 3+.
        </p>
      </div>
    </div>
  );
}
