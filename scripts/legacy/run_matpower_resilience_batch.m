function run_matpower_resilience_batch(input_mat, output_mat)
%RUN_MATPOWER_RESILIENCE_BATCH
% Batch OPF evaluation using MATPOWER.
%
% Inputs (loaded from input_mat):
%   contingencies         [S x T x L], 1 means branch outage
%   typical_scenarios     [N x T x 2], col1=wind speed (m/s), col2=PV total (MW)
%   load_bus_ids          [K x 1], bus numbers in case30 (1-based)
%   load_demands_mw       [K x 1], active power demand in MW
%   load_priority_weights [K x 1], priority weights (4/2/1 style)
%
% Outputs (saved to output_mat):
%   indicator_tensor      [N x S x 6], indicators R1..R6
%   opf_success_rate      scalar, successful OPF ratio over all (N,S,T)

if nargin < 2
    error('Usage: run_matpower_resilience_batch(input_mat, output_mat)');
end

define_constants;
data = load(input_mat);

contingencies = data.contingencies;
typical_scenarios = data.typical_scenarios;
load_bus_ids = data.load_bus_ids(:);
load_demands = data.load_demands_mw(:);
load_weights = data.load_priority_weights(:);

[n_cont, n_t, n_branch] = size(contingencies);
[n_sce, n_t2, n_dim] = size(typical_scenarios);
if n_t ~= n_t2
    error('Time dimension mismatch between contingencies and scenarios.');
end
if n_dim < 2
    error('typical_scenarios third dimension must be at least 2.');
end

mpc_base = loadcase('case30');
if size(mpc_base.branch, 1) ~= n_branch
    error('Branch count mismatch: case30 has %d branches, but contingencies use %d.', size(mpc_base.branch, 1), n_branch);
end

% Keep only modeled loads on selected buses (to align with Python-side load list).
mpc_base.bus(:, PD) = 0;
mpc_base.bus(:, QD) = 0;
pf_load = 0.95;
q_factor = tan(acos(pf_load));
for k = 1:length(load_bus_ids)
    bus_k = load_bus_ids(k);
    mpc_base.bus(bus_k, PD) = load_demands(k);
    mpc_base.bus(bus_k, QD) = load_demands(k) * q_factor;
end

% Convert fixed loads to dispatchable loads with priority-based VOLL.
% Higher weight -> higher VOLL -> less likely to be shed in OPF.
voll_base = 10000;
voll = voll_base * (load_weights ./ max(min(load_weights), eps));
mpc_base = load2disp(mpc_base, '', load_bus_ids, voll);

% Locate dispatchable-load generator rows corresponding to target load buses.
load_gen_idx = zeros(length(load_bus_ids), 1);
mask_is_load = isload(mpc_base.gen);
for k = 1:length(load_bus_ids)
    idx = find(mask_is_load & mpc_base.gen(:, GEN_BUS) == load_bus_ids(k), 1, 'first');
    if isempty(idx)
        error('Cannot find dispatchable load generator for bus %d.', load_bus_ids(k));
    end
    load_gen_idx(k) = idx;
end

% Add renewable generators at buses used in the paper setup.
% Wind farms: bus 21, 30
% PV stations: bus 5, 12
ren_buses = [21, 30, 5, 12];
n_ren = numel(ren_buses);

template_gen = mpc_base.gen(1, :);
new_gen = repmat(template_gen, n_ren, 1);
for k = 1:n_ren
    new_gen(k, :) = 0;
    new_gen(k, GEN_BUS) = ren_buses(k);
    new_gen(k, PG) = 0;
    new_gen(k, QG) = 0;
    new_gen(k, QMAX) = 100;
    new_gen(k, QMIN) = -100;
    new_gen(k, VG) = 1;
    new_gen(k, MBASE) = 100;
    new_gen(k, GEN_STATUS) = 1;
    new_gen(k, PMAX) = 0;
    new_gen(k, PMIN) = 0;
end
mpc_base.gen = [mpc_base.gen; new_gen];
ren_gen_idx = (size(mpc_base.gen, 1) - n_ren + 1):size(mpc_base.gen, 1);

template_cost = mpc_base.gencost(1, :);
new_cost = repmat(template_cost, n_ren, 1);
new_cost(:, 1) = 2;   % polynomial model
new_cost(:, 2) = 0;   % startup
new_cost(:, 3) = 0;   % shutdown
if size(new_cost, 2) >= 4
    new_cost(:, 4) = 3; % n = 3 (quadratic form)
end
if size(new_cost, 2) >= 5
    new_cost(:, 5:end) = 0;
end
mpc_base.gencost = [mpc_base.gencost; new_cost];

indicator_tensor = zeros(n_sce, n_cont, 6);
opf_success_count = 0;
opf_total = n_sce * n_cont * n_t;

mpopt_ac = mpoption('verbose', 0, 'out.all', 0, 'opf.ac.solver', 'MIPS');
mpopt_dc = mpoption('verbose', 0, 'out.all', 0, 'model', 'DC');

for s_idx = 1:n_sce
    for c_idx = 1:n_cont
        shed_matrix = zeros(n_t, length(load_bus_ids));

        for t = 1:n_t
            mpc_t = mpc_base;
            out_mask = squeeze(contingencies(c_idx, t, :)) > 0.5;
            mpc_t.branch(out_mask, BR_STATUS) = 0;

            wind_speed = max(typical_scenarios(s_idx, t, 1), 0);
            pv_total = min(max(typical_scenarios(s_idx, t, 2), 0), 20);

            wind_one_farm = wind_power_curve_single_farm(wind_speed);
            p_wind_21 = wind_one_farm;
            p_wind_30 = wind_one_farm;
            p_pv_5 = 0.75 * pv_total;
            p_pv_12 = 0.25 * pv_total;
            ren_pmax = [p_wind_21; p_wind_30; p_pv_5; p_pv_12];

            mpc_t.gen(ren_gen_idx, PMAX) = ren_pmax;
            mpc_t.gen(ren_gen_idx, PMIN) = 0;
            mpc_t.gen(ren_gen_idx, PG) = ren_pmax;

            res = runopf(mpc_t, mpopt_ac);
            if ~res.success
                res = rundcopf(mpc_t, mpopt_dc);
            end

            if res.success
                opf_success_count = opf_success_count + 1;
                pg_disp = res.gen(load_gen_idx, PG)';
                served = max(-pg_disp(:), 0);
                shed = max(load_demands - served, 0);
            else
                % Conservative fallback if both AC and DC OPF fail.
                shed = load_demands;
            end

            shed_matrix(t, :) = shed';
        end

        indicator_tensor(s_idx, c_idx, :) = compute_indicators_from_shed(shed_matrix, load_weights);
    end
end

opf_success_rate = opf_success_count / max(opf_total, 1);
save(output_mat, 'indicator_tensor', 'opf_success_rate');

end


function p_mw = wind_power_curve_single_farm(v_ms)
% Wind farm power model consistent with the Python-side formula.
vci = 3.0;
vr = 12.0;
vco = 25.0;
rated_per_turbine = 2.0;  % MW
n_turbines = 10;
p_rated = rated_per_turbine * n_turbines;

if v_ms <= vci || v_ms > vco
    p_mw = 0.0;
elseif v_ms <= vr
    p_mw = p_rated * (v_ms^3 - vci^3) / max(vr^3 - vci^3, 1e-9);
else
    p_mw = p_rated;
end
end


function ind = compute_indicators_from_shed(shed_matrix, load_weights)
% Compute R1..R6 from per-time-step shed matrix.
% shed_matrix: [T x K]

total_shed_t = sum(shed_matrix, 2);
total_shed = sum(total_shed_t);
node_total_shed = sum(shed_matrix, 1);

if total_shed > 1e-9
    r1 = sum(load_weights(:)' .* node_total_shed) / total_shed;
else
    r1 = 1.0;
end

r2 = sum(total_shed_t);
r3 = max(total_shed_t);

idx = find(total_shed_t > 1e-9);
if isempty(idx)
    t_len = size(shed_matrix, 1);
    r4 = t_len - 1;
    r5 = 0.0;
    r6 = 0.0;
else
    t1 = idx(1);
    t4 = idx(end);
    [~, t2] = max(total_shed_t);
    t3 = t2;
    r4 = max(t2 - t1, 0);
    r5 = max(t4 - t3, 0);
    r6 = max(t4 - t1, 0);
end

ind = [r1, r2, r3, r4, r5, r6];
end
